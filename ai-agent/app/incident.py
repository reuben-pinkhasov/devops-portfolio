from datetime import datetime, timezone


def correlate_incidents(nodes, pods, events, findings):
    """
    Correlate Kubernetes findings into higher-level incidents.
    """

    incidents = []

    # ---------------------------------------------------------
    # Incident: Unreachable Kubernetes node
    # ---------------------------------------------------------

    for node in nodes:
        unreachable = any(
            taint["key"] == "node.kubernetes.io/unreachable"
            for taint in node["taints"]
        )

        if node["ready"] != "True" and unreachable:

            affected_pods = [
                pod["name"]
                for pod in pods
                if pod["phase"] == "Pending"
            ]

            scheduling_failures = [
                event
                for event in events
                if (
                    event["reason"] == "FailedScheduling"
                    and event["type"] == "Warning"
                )
            ]

            incidents.append(
                {
                    "id": "INC-NODE-001",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": "CRITICAL",
                    "category": "NODE_UNAVAILABLE",
                    "title": "Kubernetes node is unreachable",

                    "root_cause": (
                        f"Node {node['name']} is not Ready "
                        "and has an unreachable taint."
                    ),

                    "impact": (
                        "Pods requiring this node cannot be scheduled. "
                        "Existing workloads on the affected node may "
                        "also become unavailable."
                    ),

                    "affected_resources": {
                        "node": node["name"],
                        "pending_pods": affected_pods,
                    },

                    "evidence": {
                        "node_ready": node["ready"],
                        "node_taints": node["taints"],
                        "failed_scheduling_events": len(
                            scheduling_failures
                        ),
                    },

                    "confidence": 0.98,

                    "recommended_actions": [
                        "Check EKS node health.",
                        "Check kubelet status and node connectivity.",
                        "Check EC2 instance health.",
                        "Check node networking.",
                        "Review recent Kubernetes and AWS events.",
                    ],
                }
            )

    return incidents