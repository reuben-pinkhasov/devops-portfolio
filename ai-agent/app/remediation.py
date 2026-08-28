from typing import Any, Dict, List


def build_remediation_plan(
    incidents: List[Dict[str, Any]],
    deep_evidence: Dict[str, Any],
    aws_evidence: List[Dict[str, Any]],
    cloudwatch_evidence: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build a safe, read-only remediation plan.

    IMPORTANT:
    This function only recommends actions.
    It does NOT execute kubectl or AWS commands.
    """

    plans = []

    for incident in incidents:

        category = incident.get("category")

        if category != "NODE_UNAVAILABLE":
            continue

        node_name = incident.get(
            "affected_resources", {}
        ).get("node")

        pending_pods = incident.get(
            "affected_resources", {}
        ).get("pending_pods", [])

        # -----------------------------------------------------
        # AWS evidence
        # -----------------------------------------------------

        aws_instance = None

        if aws_evidence:

            aws_instance = aws_evidence[0].get(
                "ec2"
            )

        instance_id = (
            aws_instance.get("instance_id")
            if aws_instance
            else None
        )

        instance_state = (
            aws_instance.get("state")
            if aws_instance
            else None
        )

        # -----------------------------------------------------
        # CloudWatch evidence
        # -----------------------------------------------------

        status_checks_ok = True

        status_metrics = (
            cloudwatch_evidence
            .get("metrics", {})
            .get("status_check_failed", {})
            .get("values", [])
        )

        if status_metrics:

            status_checks_ok = all(
                value == 0
                for value in status_metrics
            )

        # -----------------------------------------------------
        # STEP 1
        # -----------------------------------------------------

        plans.append(
            {
                "step": 1,
                "priority": "CRITICAL",
                "action": "Verify Kubernetes node state",
                "description": (
                    "Inspect the node conditions, "
                    "taints and recent Kubernetes events."
                ),
                "commands": [
                    f"kubectl describe node {node_name}",
                    f"kubectl get node {node_name} -o wide",
                ],
                "risk": "LOW",
                "automatic_execution": False,
                "reason": (
                    "The node is currently reported "
                    "as unreachable by Kubernetes."
                ),
            }
        )

        # -----------------------------------------------------
        # STEP 2
        # -----------------------------------------------------

        plans.append(
            {
                "step": 2,
                "priority": "HIGH",
                "action": "Check EC2 instance health",
                "description": (
                    "Verify that the EC2 instance backing "
                    "the Kubernetes node is running and "
                    "passing AWS status checks."
                ),
                "commands": [
                    (
                        "aws ec2 describe-instance-status "
                        f"--instance-ids {instance_id}"
                    )
                    if instance_id
                    else (
                        "aws ec2 describe-instance-status "
                        "--include-all-instances"
                    )
                ],
                "risk": "LOW",
                "automatic_execution": False,
                "evidence": {
                    "instance_state": instance_state,
                    "status_checks_ok":
                        status_checks_ok,
                },
                "reason": (
                    "AWS infrastructure health should be "
                    "confirmed before any remediation."
                ),
            }
        )

        # -----------------------------------------------------
        # STEP 3
        # -----------------------------------------------------

        plans.append(
            {
                "step": 3,
                "priority": "HIGH",
                "action": "Check kubelet and node connectivity",
                "description": (
                    "If the EC2 instance is accessible, "
                    "investigate kubelet health and "
                    "connectivity to the EKS control plane."
                ),
                "commands": [
                    "systemctl status kubelet",
                    "journalctl -u kubelet --since '1 hour ago'",
                ],
                "risk": "LOW",
                "automatic_execution": False,
                "reason": (
                    "Kubernetes reports the node as "
                    "unreachable, but the exact node-level "
                    "cause has not yet been established."
                ),
            }
        )

        # -----------------------------------------------------
        # STEP 4
        # -----------------------------------------------------

        if pending_pods:

            plans.append(
                {
                    "step": 4,
                    "priority": "HIGH",
                    "action": "Investigate pending workloads",
                    "description": (
                        "Determine why affected pods cannot "
                        "be scheduled."
                    ),
                    "commands": [
                        f"kubectl describe pod {pod} "
                        "-n devops-demo"
                        for pod in pending_pods
                    ],
                    "risk": "LOW",
                    "automatic_execution": False,
                    "reason": (
                        "Pending pods show that the node "
                        "failure is affecting workload "
                        "scheduling."
                    ),
                }
            )

        # -----------------------------------------------------
        # STEP 5
        # -----------------------------------------------------

        plans.append(
            {
                "step": 5,
                "priority": "MEDIUM",
                "action": "Verify cluster capacity",
                "description": (
                    "Determine whether another healthy "
                    "worker node is available to run "
                    "the affected workloads."
                ),
                "commands": [
                    "kubectl get nodes -o wide",
                    "kubectl get pods -A -o wide",
                ],
                "risk": "LOW",
                "automatic_execution": False,
                "reason": (
                    "A second healthy node would allow "
                    "Kubernetes to reschedule workloads "
                    "without modifying the failed node."
                ),
            }
        )

        # -----------------------------------------------------
        # STEP 6
        # -----------------------------------------------------

        plans.append(
            {
                "step": 6,
                "priority": "MEDIUM",
                "action": "Review CloudWatch metrics",
                "description": (
                    "Check CPU, network and EC2 status "
                    "metrics around the incident window."
                ),
                "commands": [
                    (
                        "aws cloudwatch get-metric-statistics "
                        "--namespace AWS/EC2 "
                        "--metric-name CPUUtilization "
                        "--dimensions "
                        f"Name=InstanceId,Value={instance_id}"
                    )
                    if instance_id
                    else (
                        "Review AWS/EC2 CloudWatch metrics"
                    )
                ],
                "risk": "LOW",
                "automatic_execution": False,
                "reason": (
                    "CloudWatch can help distinguish "
                    "infrastructure failure from a "
                    "Kubernetes/kubelet problem."
                ),
            }
        )

        # -----------------------------------------------------
        # STEP 7 — destructive actions explicitly disabled
        # -----------------------------------------------------

        plans.append(
            {
                "step": 7,
                "priority": "CAUTION",
                "action": "Do NOT automatically delete or terminate the node",
                "description": (
                    "Do not remove the Kubernetes node or "
                    "terminate the EC2 instance until the "
                    "underlying cause has been investigated."
                ),
                "commands": [],
                "risk": "HIGH",
                "automatic_execution": False,
                "reason": (
                    "Deleting or terminating the node could "
                    "destroy useful diagnostic evidence and "
                    "may cause additional workload disruption."
                ),
            }
        )

    return plans