import json
#from agent import analyze_incident

from .kubernetes_tools import (
    get_pods,
    get_deployments,
    get_services,
    get_events,
    get_hpa,
    get_nodes,
)

from .diagnose import diagnose
from .incident import correlate_incidents
from .agent import analyze
from .aws_tools import investigate_node as investigate_aws_node
from .correlator import correlate_incidents_with_aws
from .remediation import build_remediation_plan
from .cloudwatch import investigate_cloudwatch
from .ai_validator import validate_ai_result
from .report import print_sre_report

from .k8s_investigation import (
    investigate_pod,
    investigate_node as investigate_k8s_node,
)


# =========================================================
# CONFIGURATION
# =========================================================

NAMESPACE = "devops-demo"
AWS_REGION = "us-east-1"


# =========================================================
# UTILITY
# =========================================================

def print_json(title, data):
    """Print data as formatted JSON."""

    print(f"\n=== {title} ===")

    print(
        json.dumps(
            data,
            indent=2,
            default=str,
        )
    )


# =========================================================
# DEEP KUBERNETES INVESTIGATION
# =========================================================

def enrich_incidents_with_kubernetes(incidents):
    """
    Perform deep Kubernetes investigation for
    affected nodes and pods.
    """

    enriched_incidents = []

    for incident in incidents:

        incident_copy = incident.copy()

        affected_resources = incident.get(
            "affected_resources",
            {},
        )

        # -----------------------------------------------------
        # Investigate affected node
        # -----------------------------------------------------

        node_name = affected_resources.get(
            "node"
        )

        if node_name:

            print(
                "\nDeep Kubernetes investigation "
                f"for node: {node_name}"
            )

            node_evidence = investigate_k8s_node(
                node_name
            )

            incident_copy[
                "kubernetes_node_evidence"
            ] = node_evidence

        # -----------------------------------------------------
        # Investigate affected pods
        # -----------------------------------------------------

        pending_pods = affected_resources.get(
            "pending_pods",
            [],
        )

        pod_evidence = []

        for pod_name in pending_pods:

            print(
                "\nDeep Kubernetes investigation "
                f"for pod: {pod_name}"
            )

            pod_result = investigate_pod(
                pod_name,
                NAMESPACE,
            )

            pod_evidence.append(
                pod_result
            )

        incident_copy[
            "kubernetes_pod_evidence"
        ] = pod_evidence

        enriched_incidents.append(
            incident_copy
        )

    return enriched_incidents


# =========================================================
# AWS INVESTIGATION
# =========================================================

def enrich_incidents_with_aws(incidents):
    """
    Add AWS infrastructure evidence to incidents
    associated with Kubernetes nodes.
    """

    enriched_incidents = []

    for incident in incidents:

        incident_copy = incident.copy()

        affected_resources = incident.get(
            "affected_resources",
            {},
        )

        node_name = affected_resources.get(
            "node"
        )

        if node_name:

            print(
                "\nInvestigating AWS infrastructure "
                f"for node: {node_name}"
            )

            aws_evidence = investigate_aws_node(
                node_name
            )

            incident_copy[
                "aws_evidence"
            ] = aws_evidence

        enriched_incidents.append(
            incident_copy
        )

    return enriched_incidents


# =========================================================
# CLOUDWATCH INVESTIGATION
# =========================================================

def investigate_incident_cloudwatch(incidents):
    """
    Investigate CloudWatch metrics for the EC2
    instance associated with an affected Kubernetes node.

    Returns:
        CloudWatch evidence dictionary.
    """

    if not incidents:
        return {}

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

        instance_id = ec2.get(
            "instance_id"
        )

        if not instance_id:
            continue

        print(
            "\nInvestigating CloudWatch metrics..."
        )

        return investigate_cloudwatch(
            instance_id=instance_id,
            region=AWS_REGION,
            period_hours=1,
        )

    return {}


# =========================================================
# ATTACH CLOUDWATCH EVIDENCE
# =========================================================

def attach_cloudwatch_evidence(
    incidents,
    cloudwatch_evidence,
):
    """
    Attach CloudWatch evidence directly to the
    corresponding incident.

    This allows the remediation layer and AI layer
    to receive the same evidence package.
    """

    enriched_incidents = []

    for incident in incidents:

        incident_copy = incident.copy()

        incident_copy[
            "cloudwatch_evidence"
        ] = cloudwatch_evidence

        enriched_incidents.append(
            incident_copy
        )

    return enriched_incidents


# =========================================================
# MAIN INVESTIGATION PIPELINE
# =========================================================

def run_investigation():
    """
    Execute the complete DevOps troubleshooting pipeline.

    Pipeline:

        Kubernetes collection
              ↓
        Deterministic diagnostics
              ↓
        Incident correlation
              ↓
        Deep Kubernetes investigation
              ↓
        AWS investigation
              ↓
        Kubernetes + AWS correlation
              ↓
        CloudWatch investigation
              ↓
        Remediation planning
              ↓
        AI SRE analysis
              ↓
        AI validation

    Returns:
        Dictionary containing the complete investigation result.
    """

    print(
        "\n" + "=" * 70
    )

    print(
        "             DEVOPS AI TROUBLESHOOTING AGENT"
    )

    print(
        "=" * 70
    )

    # =====================================================
    # 1. COLLECT KUBERNETES DATA
    # =====================================================

    print(
        "\nCollecting Kubernetes data..."
    )

    pods = get_pods(
        NAMESPACE
    )

    print("✓ Pods")

    nodes = get_nodes()

    print("✓ Nodes")

    deployments = get_deployments(
        NAMESPACE
    )

    print("✓ Deployments")

    services = get_services(
        NAMESPACE
    )

    print("✓ Services")

    events = get_events()

    print("✓ Events")

    hpa = get_hpa(
        NAMESPACE
    )

    print("✓ HPA")

    # =====================================================
    # 2. DISPLAY KUBERNETES DATA
    # =====================================================

    print_json(
        "PODS",
        pods,
    )

    print_json(
        "NODES",
        nodes,
    )

    print_json(
        "DEPLOYMENTS",
        deployments,
    )

    print_json(
        "SERVICES",
        services,
    )

    print_json(
        "EVENTS",
        events,
    )

    print_json(
        "HPA",
        hpa,
    )

    # =====================================================
    # 3. DETERMINISTIC DIAGNOSTICS
    # =====================================================

    print(
        "\nRunning deterministic diagnostics..."
    )

    findings = diagnose(
        nodes=nodes,
        pods=pods,
        events=events,
    )

    print(
        f"✓ {len(findings)} findings detected"
    )

    print_json(
        "DIAGNOSTIC FINDINGS",
        findings,
    )

    # =====================================================
    # 4. INCIDENT CORRELATION
    # =====================================================

    print(
        "\nCorrelating incidents..."
    )

    incidents = correlate_incidents(
        nodes=nodes,
        pods=pods,
        events=events,
        findings=findings,
    )

    print(
        f"✓ {len(incidents)} incident(s) detected"
    )

    print_json(
        "INCIDENTS",
        incidents,
    )

    # =====================================================
    # STOP IF NO INCIDENTS
    # =====================================================

    if not incidents:

        print(
            "\nNo incidents detected."
        )

        return {
            "incidents": [],
            "findings": findings,
            "remediation_plan": {},
            "cloudwatch_evidence": {},
            "ai_result": {},
        }

    # =====================================================
    # 5. DEEP KUBERNETES INVESTIGATION
    # =====================================================

    print(
        "\nStarting deep Kubernetes investigation..."
    )

    incidents = enrich_incidents_with_kubernetes(
        incidents
    )

    print_json(
        "DEEP KUBERNETES EVIDENCE",
        incidents,
    )

    # =====================================================
    # 6. AWS INVESTIGATION
    # =====================================================

    print(
        "\nStarting AWS infrastructure investigation..."
    )

    incidents = enrich_incidents_with_aws(
        incidents
    )

    print_json(
        "AWS EVIDENCE",
        incidents,
    )

    # =====================================================
    # 7. KUBERNETES + AWS CORRELATION
    # =====================================================

    print(
        "\nCorrelating Kubernetes and AWS evidence..."
    )

    incidents = correlate_incidents_with_aws(
        incidents
    )

    print_json(
        "CORRELATED INCIDENTS",
        incidents,
    )

    # =====================================================
    # 8. CLOUDWATCH INVESTIGATION
    # =====================================================

    print(
        "\nStarting CloudWatch investigation..."
    )

    cloudwatch_evidence = (
        investigate_incident_cloudwatch(
            incidents
        )
    )

    print_json(
        "CLOUDWATCH EVIDENCE",
        cloudwatch_evidence,
    )

    # -----------------------------------------------------
    # Attach CloudWatch evidence to incidents
    # -----------------------------------------------------

    incidents = attach_cloudwatch_evidence(
        incidents,
        cloudwatch_evidence,
    )

    print_json(
        "INCIDENTS WITH CLOUDWATCH EVIDENCE",
        incidents,
    )

    # =====================================================
    # 9. REMEDIATION PLANNER
    # =====================================================

    print(
        "\nBuilding remediation plan..."
    )

    aws_evidence = []

    if incidents:

        aws_evidence = incidents[0].get(
            "aws_evidence",
            [],
        )

    remediation_plan = (
        build_remediation_plan(
            incidents=incidents,

            deep_evidence={
                "incidents": incidents,
            },

            aws_evidence=aws_evidence,

            cloudwatch_evidence=(
                cloudwatch_evidence
            ),
        )
    )

    print_json(
        "REMEDIATION PLAN",
        remediation_plan,
    )

    # =====================================================
    # 10. AI SRE ANALYSIS
    # =====================================================

    print(
        "\nCalling Amazon Bedrock..."
    )

    ai_input = {
        "incidents": incidents,

        "remediation_plan": (
            remediation_plan
        ),
    }

    ai_result = analyze(
        ai_input
    )

    # =====================================================
    # 11. VALIDATE AI RESULT
    # =====================================================

    if isinstance(
        ai_result,
        dict,
    ):

        ai_result = validate_ai_result(
            ai_result,
            incidents,
        )

    else:

        ai_result = {
            "error": (
                "AI analysis returned "
                "an unexpected result."
            ),
            "raw_result": str(
                ai_result
            ),
        }

    # =====================================================
    # 12. DISPLAY AI ANALYSIS
    # =====================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "                       AI SRE ANALYSIS"
    )

    print(
        "=" * 70
    )

    print_json(
        "AI RESULT",
        ai_result,
    )

    # =====================================================
    # 12.1 COMPACT SRE REPORT
    # =====================================================

    print_sre_report(
        ai_result
    )
        
    # =====================================================
    # 13. BUILD FINAL JSON REPORT
    # =====================================================

    report = {
        "agent": {
            "name": (
                "DevOps AI Troubleshooting Agent"
            ),
            "namespace": NAMESPACE,
            "aws_region": AWS_REGION,
        },

        "kubernetes": {
            "pods": pods,
            "nodes": nodes,
            "deployments": deployments,
            "services": services,
            "events": events,
            "hpa": hpa,
        },

        "diagnostics": {
            "findings": findings,
        },

        "incidents": incidents,

        "remediation_plan": (
            remediation_plan
        ),

        "ai_analysis": ai_result,
    }

    # =====================================================
    # 14. PRINT FINAL JSON REPORT
    # =====================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "                    FINAL JSON REPORT"
    )

    print(
        "=" * 70
    )

    print_json(
        "FINAL REPORT",
        report,
    )

    return report


# =========================================================
# ENTRY POINT
# =========================================================

def main():

    run_investigation()


if __name__ == "__main__":

    main()