import json


def _latest_metric(metrics, metric_name):
    """
    Return the latest CloudWatch metric value.
    """

    metric = metrics.get(metric_name)

    if not metric:
        return None

    values = metric.get("values", [])

    if not values:
        return None

    return values[0]


def analyze_cloudwatch(cloudwatch):
    """
    Convert raw CloudWatch metrics into deterministic
    observations.
    """

    findings = []

    if not cloudwatch:
        return findings

    metrics = cloudwatch.get(
        "metrics",
        {},
    )

    # ---------------------------------------------------------
    # EC2 status checks
    # ---------------------------------------------------------

    status_failed = _latest_metric(
        metrics,
        "status_check_failed",
    )

    instance_failed = _latest_metric(
        metrics,
        "status_check_failed_instance",
    )

    system_failed = _latest_metric(
        metrics,
        "status_check_failed_system",
    )

    if status_failed == 0:

        findings.append(
            {
                "category": "AWS_HEALTH",
                "severity": "INFO",
                "finding": (
                    "EC2 StatusCheckFailed is 0. "
                    "No EC2 status-check failure was "
                    "observed in the sampled period."
                ),
                "evidence": {
                    "StatusCheckFailed": status_failed,
                },
            }
        )

    if instance_failed == 0:

        findings.append(
            {
                "category": "AWS_HEALTH",
                "severity": "INFO",
                "finding": (
                    "EC2 instance status checks are healthy."
                ),
                "evidence": {
                    "StatusCheckFailed_Instance":
                        instance_failed,
                },
            }
        )

    if system_failed == 0:

        findings.append(
            {
                "category": "AWS_HEALTH",
                "severity": "INFO",
                "finding": (
                    "EC2 system status checks are healthy."
                ),
                "evidence": {
                    "StatusCheckFailed_System":
                        system_failed,
                },
            }
        )

    # ---------------------------------------------------------
    # CPU
    # ---------------------------------------------------------

    cpu = _latest_metric(
        metrics,
        "cpu",
    )

    if cpu is not None:

        if cpu > 90:

            findings.append(
                {
                    "category": "AWS_RESOURCE_PRESSURE",
                    "severity": "HIGH",
                    "finding": (
                        "EC2 CPU utilization is "
                        "very high."
                    ),
                    "evidence": {
                        "CPUUtilization": cpu,
                    },
                }
            )

        elif cpu < 80:

            findings.append(
                {
                    "category": "AWS_RESOURCE_HEALTH",
                    "severity": "INFO",
                    "finding": (
                        "EC2 CPU utilization is "
                        "not showing obvious saturation."
                    ),
                    "evidence": {
                        "CPUUtilization": cpu,
                    },
                }
            )

    # ---------------------------------------------------------
    # Network
    # ---------------------------------------------------------

    network_in = _latest_metric(
        metrics,
        "network_in",
    )

    network_out = _latest_metric(
        metrics,
        "network_out",
    )

    if network_in and network_in > 0:

        findings.append(
            {
                "category": "AWS_NETWORK",
                "severity": "INFO",
                "finding": (
                    "EC2 NetworkIn has recent "
                    "non-zero traffic."
                ),
                "evidence": {
                    "NetworkIn": network_in,
                },
            }
        )

    if network_out and network_out > 0:

        findings.append(
            {
                "category": "AWS_NETWORK",
                "severity": "INFO",
                "finding": (
                    "EC2 NetworkOut has recent "
                    "non-zero traffic."
                ),
                "evidence": {
                    "NetworkOut": network_out,
                },
            }
        )

    return findings


def correlate_incidents_with_aws(
    incidents,
):
    """
    Correlate Kubernetes incidents with AWS
    and CloudWatch evidence.
    """

    enriched = []

    for incident in incidents:

        incident_copy = incident.copy()

        correlations = []

        # =====================================================
        # AWS EVIDENCE
        # =====================================================

        aws_evidence = incident.get(
            "aws_evidence",
            [],
        )

        for aws_item in aws_evidence:

            ec2 = aws_item.get(
                "ec2",
                {}
            )

            status_checks = aws_item.get(
                "status_checks",
                []
            )

            # -------------------------------------------------
            # EC2 state
            # -------------------------------------------------

            state = ec2.get(
                "state"
            )

            if state == "running":

                correlations.append(
                    {
                        "category": "EC2_STATE",
                        "severity": "INFO",
                        "finding": (
                            "The EC2 instance associated "
                            "with the Kubernetes node "
                            "is running."
                        ),
                        "evidence": {
                            "instance_id":
                                ec2.get(
                                    "instance_id"
                                ),
                            "state": state,
                        },
                    }
                )

            # -------------------------------------------------
            # EC2 status checks
            # -------------------------------------------------

            for check in status_checks:

                if (
                    check.get("system_status")
                    == "ok"
                    and
                    check.get("instance_status")
                    == "ok"
                ):

                    correlations.append(
                        {
                            "category":
                                "EC2_HEALTH",
                            "severity":
                                "INFO",
                            "finding": (
                                "EC2 system and "
                                "instance status "
                                "checks are healthy."
                            ),
                            "evidence":
                                check,
                        }
                    )

            # -------------------------------------------------
            # CloudWatch
            # -------------------------------------------------

            cloudwatch = aws_item.get(
                "cloudwatch"
            )

            if cloudwatch:

                cw_findings = (
                    analyze_cloudwatch(
                        cloudwatch
                    )
                )

                correlations.extend(
                    cw_findings
                )

        # =====================================================
        # CROSS-LAYER CORRELATION
        # =====================================================

        node = (
            incident
            .get(
                "affected_resources",
                {}
            )
            .get(
                "node"
            )
        )

        if node:

            # Determine whether AWS health evidence
            # contradicts an obvious EC2 failure.

            ec2_healthy = any(
                finding.get("category")
                == "EC2_HEALTH"
                for finding in correlations
            )

            status_healthy = any(
                finding.get("category")
                == "AWS_HEALTH"
                for finding in correlations
            )

            node_unreachable = (
                incident.get(
                    "category"
                )
                == "NODE_UNAVAILABLE"
            )

            if (
                node_unreachable
                and ec2_healthy
                and status_healthy
            ):

                correlations.append(
                    {
                        "category":
                            "CROSS_LAYER_CORRELATION",

                        "severity":
                            "HIGH",

                        "finding": (
                            "Kubernetes reports the "
                            "node as unreachable, "
                            "while EC2 and CloudWatch "
                            "health evidence does not "
                            "show an obvious EC2 "
                            "infrastructure failure."
                        ),

                        "evidence": {
                            "kubernetes_node":
                                node,

                            "ec2_health":
                                "healthy",

                            "cloudwatch_health":
                                "healthy",
                        },

                        "investigation_priority": [
                            "kubelet",
                            "node-to-EKS-control-plane "
                            "connectivity",
                            "node networking",
                            "OS-level health",
                        ],
                    }
                )

        incident_copy[
            "correlations"
        ] = correlations

        enriched.append(
            incident_copy
        )

    return enriched


if __name__ == "__main__":

    print(
        "Correlation engine loaded."
    )