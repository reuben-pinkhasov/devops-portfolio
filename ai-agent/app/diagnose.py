def diagnose_nodes(nodes):
    """
    Analyze Kubernetes node health.
    """

    findings = []

    for node in nodes:
        name = node["name"]
        ready = node["ready"]
        taints = node["taints"]

        unreachable_taints = [
            taint
            for taint in taints
            if taint["key"] == "node.kubernetes.io/unreachable"
        ]

        if ready != "True":
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "NODE_HEALTH",
                    "resource": name,
                    "finding": (
                        f"Node {name} is not Ready "
                        f"(status: {ready})."
                    ),
                    "evidence": {
                        "ready": ready,
                        "taints": taints,
                    },
                }
            )

        if unreachable_taints:
            findings.append(
                {
                    "severity": "CRITICAL",
                    "category": "NODE_CONNECTIVITY",
                    "resource": name,
                    "finding": (
                        f"Node {name} has "
                        "node.kubernetes.io/unreachable "
                        "taints."
                    ),
                    "evidence": unreachable_taints,
                }
            )

    return findings

def diagnose_events(events):
    """
    Analyze Kubernetes warning events.
    """

    findings = []

    for event in events:
        if event["type"] != "Warning":
            continue

        reason = event["reason"]
        message = event["message"]

        if reason == "FailedScheduling":
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "SCHEDULING",
                    "resource": event["object"],
                    "finding": (
                        "Kubernetes failed to schedule a pod."
                    ),
                    "evidence": {
                        "message": message,
                        "count": event["count"],
                    },
                }
            )

    return findings

def diagnose_pods(pods):
    """
    Analyze Kubernetes pod states.
    """

    findings = []

    for pod in pods:
        name = pod["name"]
        phase = pod["phase"]
        restarts = pod["restarts"]

        if phase == "Pending":
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "POD_STATUS",
                    "resource": name,
                    "finding": (
                        f"Pod {name} is Pending."
                    ),
                    "evidence": {
                        "phase": phase,
                        "restarts": restarts,
                    },
                }
            )

        if restarts >= 3:
            findings.append(
                {
                    "severity": "HIGH",
                    "category": "POD_RESTARTS",
                    "resource": name,
                    "finding": (
                        f"Pod {name} has restarted "
                        f"{restarts} times."
                    ),
                    "evidence": {
                        "restarts": restarts,
                    },
                }
            )

    return findings

def diagnose(nodes, pods, events):
    """
    Run all deterministic Kubernetes diagnostics.
    """

    findings = []

    findings.extend(diagnose_nodes(nodes))
    findings.extend(diagnose_pods(pods))
    findings.extend(diagnose_events(events))

    return findings