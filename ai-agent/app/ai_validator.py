from typing import Any, Dict, List


def _get_aws_state(
    incidents: List[Dict[str, Any]],
) -> str | None:

    for incident in incidents:

        aws_evidence = incident.get(
            "aws_evidence",
            [],
        )

        if not aws_evidence:
            continue

        ec2 = aws_evidence[0].get(
            "ec2",
            {},
        )

        state = ec2.get("state")

        if state:
            return state

    return None


def _get_aws_status_checks(
    incidents: List[Dict[str, Any]],
) -> tuple[str | None, str | None]:

    for incident in incidents:

        aws_evidence = incident.get(
            "aws_evidence",
            [],
        )

        if not aws_evidence:
            continue

        status_checks = aws_evidence[0].get(
            "status_checks",
            [],
        )

        if not status_checks:
            continue

        check = status_checks[0]

        return (
            check.get("system_status"),
            check.get("instance_status"),
        )

    return None, None


def _get_node_conditions(
    incidents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    for incident in incidents:

        node_evidence = incident.get(
            "kubernetes_node_evidence",
            {},
        )

        if not isinstance(node_evidence, dict):
            continue

        conditions = node_evidence.get(
            "conditions",
            [],
        )

        if conditions:
            return conditions

    return []


def _get_pending_pods(
    incidents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    pods = []

    for incident in incidents:

        pod_evidence = incident.get(
            "kubernetes_pod_evidence",
            [],
        )

        if not isinstance(
            pod_evidence,
            list,
        ):
            continue

        for pod in pod_evidence:

            if not isinstance(
                pod,
                dict,
            ):
                continue

            pods.append(pod)

    return pods


def _get_node_name(
    incidents: List[Dict[str, Any]],
) -> str | None:

    for incident in incidents:

        affected_resources = incident.get(
            "affected_resources",
            {},
        )

        if not isinstance(
            affected_resources,
            dict,
        ):
            continue

        node = affected_resources.get(
            "node"
        )

        if node:
            return node

    return None


def validate_ai_result(
    ai_result: Dict[str, Any],
    incidents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate AI-generated conclusions against
    deterministic Kubernetes and AWS evidence.

    The AI may generate hypotheses, but it must
    not contradict deterministic evidence.
    """

    validation_errors = []
    validation_warnings = []

    # =========================================================
    # BASIC VALIDATION
    # =========================================================

    if not isinstance(
        ai_result,
        dict,
    ):

        return {
            "validation": {
                "valid": False,
                "errors": [
                    "AI result is not a dictionary."
                ],
                "warnings": [],
            }
        }

    # =========================================================
    # AWS EVIDENCE
    # =========================================================

    aws_state = _get_aws_state(
        incidents
    )

    system_status, instance_status = (
        _get_aws_status_checks(
            incidents
        )
    )

    # =========================================================
    # KUBERNETES EVIDENCE
    # =========================================================

    node_name = _get_node_name(
        incidents
    )

    node_conditions = _get_node_conditions(
        incidents
    )

    pending_pods = _get_pending_pods(
        incidents
    )

    ai_text = str(
        ai_result
    ).lower()

    # =========================================================
    # VALIDATE EC2 STATE
    # =========================================================

    if aws_state:

        if (
            aws_state == "running"
            and (
                "ec2 instance is stopped"
                in ai_text
                or "ec2 instance is terminated"
                in ai_text
            )
        ):

            validation_errors.append(
                "AI contradicted deterministic AWS "
                "evidence: EC2 instance is running."
            )

    # =========================================================
    # VALIDATE AWS STATUS CHECKS
    # =========================================================

    if (
        system_status == "ok"
        and instance_status == "ok"
    ):

        validation_warnings.append(
            "AWS system and instance status checks "
            "are healthy according to deterministic evidence."
        )

    # =========================================================
    # VALIDATE KUBERNETES NODE STATE
    # =========================================================

    if node_conditions:

        unknown_conditions = []

        for condition in node_conditions:

            if not isinstance(
                condition,
                dict,
            ):
                continue

            status = condition.get(
                "status"
            )

            if status == "Unknown":
                unknown_conditions.append(
                    condition
                )

        if unknown_conditions:

            if (
                "node is healthy"
                in ai_text
                and "unknown"
                not in ai_text
            ):

                validation_errors.append(
                    "AI appears to contradict deterministic "
                    "Kubernetes evidence: node conditions "
                    "are Unknown."
                )

            validation_warnings.append(
                "Kubernetes evidence indicates that the "
                "node is not currently reporting healthy status."
            )

    # =========================================================
    # VALIDATE KUBELET FAILURE EVIDENCE
    # =========================================================

    kubelet_evidence_found = False

    for condition in node_conditions:

        if not isinstance(
            condition,
            dict,
        ):
            continue

        message = str(
            condition.get(
                "message",
                ""
            )
        ).lower()

        reason = str(
            condition.get(
                "reason",
                ""
            )
        ).lower()

        if (
            "kubelet stopped posting node status"
            in message
            or reason == "nodestatusunknown"
        ):

            kubelet_evidence_found = True

            break

    if kubelet_evidence_found:

        validation_warnings.append(
            "Deterministic Kubernetes evidence confirms "
            "loss of kubelet status reporting. The underlying "
            "reason for the kubelet failure remains unconfirmed "
            "unless node-level logs are available."
        )

    # =========================================================
    # VALIDATE PENDING PODS
    # =========================================================

    if pending_pods:

        validation_warnings.append(
            f"{len(pending_pods)} pending pod(s) are "
            "associated with affected Kubernetes resources."
        )

    # =========================================================
    # VALIDATE CONFIDENCE
    # =========================================================

    confidence = ai_result.get(
        "confidence"
    )

    if isinstance(
        confidence,
        (int, float),
    ):

        if confidence < 0:

            validation_errors.append(
                "AI confidence cannot be negative."
            )

        if confidence > 1:

            validation_errors.append(
                "AI confidence must be between 0 and 1."
            )

    else:

        validation_warnings.append(
            "AI result does not contain a numeric confidence value."
        )

    # =========================================================
    # VALIDATE ROOT CAUSE
    # =========================================================

    root_cause = str(
        ai_result.get(
            "root_cause",
            ""
        )
    ).lower()

    if (
        kubelet_evidence_found
        and "not yet confirmed" not in root_cause
    ):

        validation_warnings.append(
            "AI provided a definitive root-cause statement "
            "even though deterministic evidence only confirms "
            "loss of kubelet status reporting."
        )

    # =========================================================
    # NODE NAME CONSISTENCY
    # =========================================================

    if node_name:

        if (
            node_name.lower()
            not in ai_text
        ):

            validation_warnings.append(
                "AI result does not explicitly reference "
                f"the affected Kubernetes node {node_name}."
            )

    # =========================================================
    # FINAL VALIDATION
    # =========================================================

    ai_result["validation"] = {
        "valid": len(
            validation_errors
        ) == 0,

        "errors": validation_errors,

        "warnings": validation_warnings,
    }

    return ai_result