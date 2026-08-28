# DevOps AI Troubleshooting Agent

AI-powered Kubernetes and AWS SRE troubleshooting agent that combines deterministic infrastructure diagnostics with Amazon Bedrock to analyze incidents, validate AI conclusions against real evidence, and produce a human-readable SRE incident report.

## 🎯 Project Overview

This project demonstrates an end-to-end **AI-assisted SRE troubleshooting workflow** for Kubernetes workloads running on AWS.

The agent collects real infrastructure data from:

* Kubernetes
* AWS EC2
* CloudWatch

It then:

1. Detects infrastructure and Kubernetes problems.
2. Correlates related incidents.
3. Performs deeper Kubernetes investigation.
4. Investigates the underlying AWS infrastructure.
5. Collects CloudWatch metrics.
6. Builds a deterministic remediation plan.
7. Sends the complete evidence package to Amazon Bedrock.
8. Generates a structured AI SRE analysis.
9. Validates the AI conclusions against deterministic evidence.
10. Produces a compact human-readable SRE report.
11. Exposes the complete workflow through FastAPI.
12. Provides a lightweight web interface for triggering investigations.

The important design principle is:

> **AI generates analysis and hypotheses, while deterministic infrastructure evidence remains the source of truth.**

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      Web Browser     │
                         │    Tiny SRE UI       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │      api.py          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Investigation      │
                         │      main.py         │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
      │  Kubernetes   │     │      AWS      │     │  CloudWatch   │
      │   Evidence    │     │ EC2 Evidence  │     │    Metrics    │
      └───────┬───────┘     └───────┬───────┘     └───────┬───────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Incident Correlation │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Remediation Planner  │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   Amazon Bedrock     │
                         │      AI / SRE        │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │    AI Validator      │
                         │ Evidence consistency│
                         └──────────┬───────────┘
                                    ▼
                    ┌──────────────────────────────┐
                    │      SRE Incident Report     │
                    │                              │
                    │ Severity                     │
                    │ Confidence                   │
                    │ Observed facts               │
                    │ Root cause assessment        │
                    │ Impact                       │
                    │ Next investigation            │
                    │ Validation                   │
                    └──────────────────────────────┘
```

---

# 🔍 What the Agent Investigates

## Kubernetes

The agent collects and analyzes:

* Pods
* Nodes
* Deployments
* Services
* Events
* HPA
* Node conditions
* Node taints
* Pending pods
* Pod scheduling problems
* Kubelet status evidence
* Kubernetes events

For affected resources it can perform deeper investigation.

Example:

```text
Node:
ip-10-0-12-130.ec2.internal

Status:
Unknown

Conditions:
MemoryPressure: Unknown
DiskPressure: Unknown
PIDPressure: Unknown
Ready: Unknown

Taints:
node.kubernetes.io/unreachable
NoSchedule
NoExecute
```

---

# ☁️ AWS Investigation

For Kubernetes nodes running on AWS EC2, the agent correlates the Kubernetes node with its EC2 instance.

It checks infrastructure evidence such as:

* EC2 instance state
* System status check
* Instance status check
* Instance identity
* AWS infrastructure information

Example deterministic evidence:

```text
EC2 instance: Running
System status check: OK
Instance status check: OK
```

This is important because it allows the agent to distinguish between:

```text
AWS infrastructure failure
            vs
Kubernetes / kubelet failure
```

---

# 📊 CloudWatch Investigation

The agent can investigate CloudWatch metrics around the incident.

This provides additional infrastructure context such as:

* CPU utilization
* Network activity
* EC2-related metrics
* Instance behavior around the incident window

CloudWatch evidence is passed into the remediation and AI analysis layers.

---

# 🤖 Amazon Bedrock

The agent sends the collected evidence to Amazon Bedrock.

The AI is instructed to produce structured JSON containing:

```json
{
  "severity": "CRITICAL",
  "title": "Kubernetes node is unreachable",
  "summary": "...",
  "root_cause": "...",
  "evidence": [],
  "remediation": [],
  "impact": "...",
  "confidence": 0.98
}
```

The model is instructed to distinguish between:

* Confirmed facts
* Root-cause hypotheses
* Recommended remediation
* Potential impact
* Confidence

---

# 🛡️ AI Result Validation

A key feature of the project is the **AI validation layer**.

The AI result is not blindly trusted.

`ai_validator.py` compares AI conclusions against deterministic Kubernetes and AWS evidence.

For example:

```text
Deterministic evidence:

EC2 = RUNNING
AWS status checks = OK
Kubernetes node = UNKNOWN
Kubelet stopped posting node status
```

If AI says:

```text
EC2 instance is terminated
```

the validator can flag this as an evidence contradiction.

The validator therefore provides:

```json
"validation": {
  "valid": true,
  "errors": [],
  "warnings": []
}
```

This creates an important SRE safety boundary:

> **The AI can interpret evidence, but it cannot override the evidence.**

---

# 🔧 Remediation Planner

The remediation layer generates structured investigation and remediation actions.

Example:

```text
1. Check Kubernetes node state
2. Check EC2 instance health
3. Investigate kubelet
4. Investigate pending workloads
5. Verify cluster capacity
6. Review CloudWatch metrics
7. Do not automatically delete or terminate the node
```

Each remediation action can contain:

* Priority
* Action
* Description
* Commands
* Risk
* Automatic execution flag
* Reason

Example:

```json
{
  "priority": "HIGH",
  "action": "Investigate kubelet",
  "risk": "LOW",
  "automatic_execution": false
}
```

The project intentionally does **not** automatically perform destructive operations.

---

# 📋 Compact SRE Incident Report

In addition to the complete JSON output, the agent produces a concise human-readable SRE report.

Example:

```text
┌──────────────────────────────────────────────────────────┐
│                    SRE INCIDENT REPORT                   │
├──────────────────────────────────────────────────────────┤
│ Severity   : CRITICAL                                    │
│ Incident   : Kubernetes node is unreachable              │
│ Confidence : 98%                                         │
├──────────────────────────────────────────────────────────┤
│ SUMMARY                                                  │
│ Kubernetes node is unreachable and workloads are         │
│ affected.                                                │
├──────────────────────────────────────────────────────────┤
│ OBSERVED                                                 │
│ • Node is unreachable                                    │
│ • Kubelet stopped posting status                         │
├──────────────────────────────────────────────────────────┤
│ ROOT CAUSE ASSESSMENT                                    │
│ Underlying cause is not yet confirmed.                   │
│                                                          │
│ Likely: Kubelet stopped reporting node status.           │
├──────────────────────────────────────────────────────────┤
│ IMPACT                                                   │
│ • Pods cannot be scheduled                               │
├──────────────────────────────────────────────────────────┤
│ NEXT INVESTIGATION / REMEDIATION                         │
│ • Check kubelet                                          │
│ • Check node connectivity                                │
├──────────────────────────────────────────────────────────┤
│ VALIDATION                                               │
│ ✓ PASS - No evidence contradictions.                    │
└──────────────────────────────────────────────────────────┘
```

This gives an SRE or interviewer a quick operational summary without requiring them to read the entire JSON report.

---

# 🚀 FastAPI

The investigation is exposed through FastAPI.

Start the API:

```bash
uvicorn app.api:app --reload
```

The API starts on:

```text
http://127.0.0.1:8000
```

## Health endpoint

```text
GET /health
```

Example:

```json
{
  "status": "healthy",
  "service": "DevOps AI Troubleshooting Agent"
}
```

## Investigation endpoint

```text
POST /investigate
```

This triggers the complete investigation pipeline and returns the structured JSON report.

## Swagger

FastAPI automatically provides interactive API documentation:

```text
/docs
```

---

# 🖥️ Tiny Web UI

A lightweight web interface can be used to trigger the investigation without manually calling the API.

The UI is intentionally simple.

The purpose is not to build a production frontend, but to demonstrate the complete DevOps/SRE workflow:

```text
Browser
   ↓
FastAPI
   ↓
Investigation
   ↓
Kubernetes
   ↓
AWS
   ↓
CloudWatch
   ↓
Bedrock
   ↓
AI Validation
   ↓
SRE Report
```

---

# 🌐 Temporary Public Demo

For demonstration purposes the local FastAPI service can be exposed using a Cloudflare Quick Tunnel.

Example:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

This produces a temporary public URL.

### Important

The Quick Tunnel is **temporary**.

It requires:

* FastAPI/Uvicorn to remain running
* Cloudflare Tunnel to remain running

The generated URL can change when the tunnel is restarted.

Therefore it should be considered a **temporary portfolio demonstration**, not a production deployment.

---

# 🧪 Running Locally

## 1. Activate virtual environment

```bash
source .venv/bin/activate
```

## 2. Start FastAPI

```bash
uvicorn app.api:app --reload
```

## 3. Open the API

```text
http://127.0.0.1:8000
```

## 4. Open Swagger

```text
http://127.0.0.1:8000/docs
```

## 5. Run investigation

Use the web UI or:

```text
POST /investigate
```

---

# 🖥️ Running the CLI Version

The complete investigation can also be executed directly:

```bash
python -m app.main
```

The CLI produces:

1. Kubernetes evidence
2. AWS evidence
3. CloudWatch evidence
4. Correlated incidents
5. Remediation plan
6. AI SRE analysis
7. Compact SRE report
8. Final JSON report

---

# 📁 Project Structure

```text
ai-agent/
│
├── app/
│   ├── api.py
│   ├── main.py
│   ├── agent.py
│   ├── report.py
│   ├── ai_validator.py
│   ├── diagnose.py
│   ├── incident.py
│   ├── correlator.py
│   ├── remediation.py
│   ├── kubernetes_tools.py
│   ├── k8s_investigation.py
│   ├── aws_tools.py
│   └── cloudwatch.py
│
├── .venv/
│
├── AI_AGENT_README.md
│
└── ...
```

---

# 🔄 End-to-End Investigation Flow

The complete workflow is:

```text
1. Collect Kubernetes data
        ↓
2. Diagnose Kubernetes state
        ↓
3. Detect incidents
        ↓
4. Correlate incidents
        ↓
5. Deep Kubernetes investigation
        ↓
6. AWS EC2 investigation
        ↓
7. CloudWatch investigation
        ↓
8. Build remediation plan
        ↓
9. Send evidence to Amazon Bedrock
        ↓
10. Generate structured AI analysis
        ↓
11. Validate AI result
        ↓
12. Generate compact SRE report
        ↓
13. Generate final JSON report
        ↓
14. Expose result through FastAPI
        ↓
15. Display through Web UI
```

---

# 💼 Why This Is Useful for an SRE / DevOps Portfolio

This project demonstrates more than simply calling an LLM.

It combines:

### Kubernetes

* Node troubleshooting
* Pod troubleshooting
* Scheduling
* Taints
* Node conditions
* Events
* HPA
* Workload investigation

### AWS

* EC2
* Instance status checks
* CloudWatch
* Kubernetes/AWS correlation

### DevOps

* Python
* FastAPI
* REST API
* Linux
* CLI tooling
* Structured JSON

### SRE

* Incident detection
* Evidence collection
* Root-cause analysis
* Remediation planning
* Risk classification
* Validation
* Operational reporting

### AI

* Amazon Bedrock
* Structured model output
* JSON parsing
* AI confidence
* Hypothesis generation
* Deterministic validation

The architecture intentionally separates:

```text
FACTS
  ↓
DETERMINISTIC ANALYSIS
  ↓
AI INTERPRETATION
  ↓
VALIDATION
  ↓
REMEDIATION
```

This is safer and more realistic than allowing an AI model to make unrestricted infrastructure decisions.

---

# ⚠️ Safety Design

The remediation engine classifies actions by risk.

For example:

```text
LOW
Investigate logs
Check node status
Inspect pods

MEDIUM
Review capacity
Review metrics

HIGH / CAUTION
Delete node
Terminate EC2 instance
```

Destructive actions are explicitly marked:

```json
"automatic_execution": false
```

The system therefore behaves as an **investigation and decision-support agent**, rather than an unrestricted autonomous infrastructure controller.

---

# 🎯 Example Incident

One demonstrated scenario is a Kubernetes node that becomes unreachable.

The observed evidence includes:

```text
Kubernetes node:
ip-10-0-12-130.ec2.internal

Node conditions:
Unknown

Taints:
node.kubernetes.io/unreachable

Kubelet:
Stopped posting node status

Pending workload:
myapp pod

AWS:
EC2 instance running
AWS status checks healthy
```

The AI analysis can therefore conclude:

```text
Severity: CRITICAL

Observed:
Kubernetes node is unreachable.

Confirmed:
Kubelet has stopped reporting node status.

Not confirmed:
The underlying reason for the kubelet failure.

Impact:
Pods may remain pending and workloads on the
affected node may become unavailable.

Next investigation:
Inspect kubelet status, node connectivity,
Kubernetes events and CloudWatch metrics.
```

This distinction between **observed evidence** and **unconfirmed root cause** is an important part of the project's SRE design.

---

# 🚧 Current Status

### Completed

* [x] Kubernetes data collection
* [x] Kubernetes diagnostics
* [x] Incident correlation
* [x] Deep Kubernetes investigation
* [x] AWS EC2 investigation
* [x] CloudWatch investigation
* [x] Remediation planner
* [x] Amazon Bedrock integration
* [x] Structured AI JSON output
* [x] Robust AI JSON parsing
* [x] AI evidence validation
* [x] Compact SRE report
* [x] Final JSON report
* [x] FastAPI API
* [x] Tiny Web UI
* [x] Local end-to-end execution
* [x] Temporary public demo through Cloudflare Quick Tunnel

### Possible Future Improvements

* [ ] Persistent production deployment
* [ ] Authentication
* [ ] Historical incident storage
* [ ] Prometheus integration
* [ ] OpenTelemetry integration
* [ ] Grafana integration
* [ ] Alertmanager integration
* [ ] Streaming investigation progress
* [ ] Incident history dashboard
* [ ] Role-based access control
* [ ] Controlled automated remediation

---

# 👨‍💻 Portfolio Objective

The goal of this project is to demonstrate how an experienced DevOps/SRE engineer can combine traditional infrastructure troubleshooting with AI-assisted analysis.

The AI is not treated as the source of truth.

Instead:

```text
Infrastructure
    ↓
Evidence
    ↓
Deterministic diagnostics
    ↓
AI analysis
    ↓
Validation against evidence
    ↓
Human-readable SRE decision support
```

This approach makes the system more suitable for real-world SRE and DevOps workflows where **accuracy, explainability and operational safety are more important than simply generating an AI answer.**
