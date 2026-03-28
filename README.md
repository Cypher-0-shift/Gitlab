# OpsOrchestrator — GitLab-Native AI SDLC Orchestration

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitLab Duo](https://img.shields.io/badge/GitLab%20Duo-Agent%20Platform-FC6D26)](https://about.gitlab.com/blog/gitlab-duo-agent-platform-complete-getting-started-guide/)
[![Anthropic](https://img.shields.io/badge/Powered%20by-Claude%20via%20GitLab%20Duo-6B4FBB)](https://www.anthropic.com)

> **Demo video:** [Watch the 3-minute demo on YouTube](https://www.youtube.com/watch?v=84L7dXv2gRk)
> <!-- ⚠️ TODO: Replace dQw4w9WgXcQ above with your actual unlisted YouTube video ID before Devpost submission -->

Converts GitLab issues and epics into complete sprint plans, security
reviews, compliance gates, and deployment readiness assessments —
fully autonomously, entirely inside GitLab.

**Core agents run natively on GitLab Duo — no infrastructure
required. Optional: GCP MCP server adds audit vaulting and
CI/CD webhooks for enterprise teams.**

Claude is accessed via the **GitLab Duo AI Gateway** (Anthropic integration).

---

## The Four Bottlenecks Solved

| Bottleneck | Agent Flow | How |
|------------|-----------|-----|
| **Planning** | `planning_flow.yml` | Decomposes issues into sprint tasks |
| **Security** | `security_flow.yml` | Scans MR diffs for vulnerabilities |
| **Compliance** | `compliance_flow.yml` | Checks policy gates before merge |
| **Deployments** | `deployment_flow.yml` | Go/no-go readiness assessment |

---

## Architecture

```
GitLab Issue / MR / Pipeline Event
           ↓
┌──────────────────────────────────┐
│    GitLab Duo Agent Platform     │
│                                  │
│  planning_flow.yml               │
│  security_flow.yml               │
│  compliance_flow.yml    →  Claude via Duo AI Gateway
│  estimation_flow.yml             │
│  dependency_flow.yml             │
│  deployment_flow.yml             │
└──────────────────────────────────┘
           ↓ native GitLab API only
┌──────────────────────────────────┐
│         GitLab Project           │
│  Issues · MRs · Pipelines        │
└──────────────────────────────────┘
```

Everything runs on GitLab's compute.
Core agents need no infrastructure. The optional GCP MCP
server (`mcp/app.py`) adds audit vaulting and webhook support.

---

## File Structure

```
ops-orchestrator/
├── flows/
│   ├── planning_flow.yml        ★ Sprint planning agent
│   ├── security_flow.yml        Security + PII scanner
│   ├── compliance_flow.yml      10-gate compliance checker
│   ├── deployment_flow.yml      Go/no-go deployment advisor
│   ├── estimation_flow.yml      Fibonacci story point estimator
│   ├── devops_flow.yml          CI/CD AutoDoctor
│   ├── standup_flow.yml         Daily digest agent
│   └── intent_router_flow.yml   Natural language router (External Agent)
├── mcp/
│   ├── app.py                   GCP Cloud Run MCP server
│   ├── mcp_config.json          MCP server registry
│   └── deploy_to_gcp.sh         One-command GCP deploy
├── agents/
│   ├── agent.yaml               Ops Orchestrator hub agent
│   └── ops_orchestrator.md      Chat agent setup guide
├── .gitlab/
│   ├── compliance_policy.yaml   Configurable policy rules
│   └── ai_config.yaml           Agent behaviour config
├── tests/
│   ├── test_flows.py            56 unit tests
│   └── test_deployment_flow.py  59 unit tests
├── docs/
│   ├── architecture.md
│   └── ADR-001-native-refactor.md
├── .gitlab-ci.yml               CI: YAML validation + tests
├── requirements.txt
├── LICENSE                      Apache 2.0
└── README.md
```

---

## Setup

### Step 1 — Set the Model (once)
```
Group Settings → GitLab Duo → Configure features
→ GitLab Duo Agent Platform → model dropdown
```
Recommended: **Claude Sonnet 4.5** | **Claude Opus 4.6** (demo)

No model string in any code file.

### Step 2 — Enable Flows
```
GitLab → Automate → Flows → New flow
Name: OpsOrchestrator | Visibility: Public
Paste: .gitlab/duo/planning_flow.yml
Enable the flow.
```
Repeat for security, compliance, estimation, dependency, deployment flows.

### Step 3 — Enable Chat Agent (optional)
```
GitLab → Automate → Agents → New agent
Name: OpsOrchestrator | Visibility: Public
Paste: the system_prompt field from agents/agent.yaml
(or follow the guide in agents/ops_orchestrator.md)
Enable all listed tools.
```

### Step 4 — Trigger
```
@ops-orchestrator plan this issue
```
Mention in any issue comment. Agent runs all steps immediately.

### Step 5 — Configure GCP MCP Server (Optional — Enterprise Audit Features)

This step enables the compliance audit vault and CI/CD webhook auto-trigger.
Core agents work without it.

**5a. Deploy the MCP server to Cloud Run:**
```bash
cd mcp
export GITLAB_PAT="glpat-xxxx"          # GitLab PAT with api scope
export GITLAB_WEBHOOK_TOKEN="my-secret" # any secret string
export DEVOPS_TRIAGE_ISSUE_IID="1"      # issue IID for CI/CD webhook comments
gcloud run deploy ops-orchestrator-gcp \
    --source . \
    --region us-central1 \
    --no-allow-unauthenticated \
    --port 8080 \
    --set-env-vars="MCP_ENV=production,GITLAB_PAT=${GITLAB_PAT},GITLAB_WEBHOOK_TOKEN=${GITLAB_WEBHOOK_TOKEN},DEVOPS_TRIAGE_ISSUE_IID=${DEVOPS_TRIAGE_ISSUE_IID}"
```

**5b. Update `.gitlab/duo/mcp.json`** with your Cloud Run URL:
```json
{
  "mcpServers": {
    "ops-orchestrator-gcp": {
      "type": "sse",
      "url": "https://YOUR-SERVICE-URL.run.app/sse",
      "description": "OpsOrchestrator GCP MCP Server — audit vault + CI/CD webhook"
    }
  }
}
```

**5c. Register GitLab Webhook:**
- GitLab → Project → Settings → Webhooks
- URL: `https://YOUR-SERVICE-URL.run.app/webhook/gitlab`
- Secret Token: your `GITLAB_WEBHOOK_TOKEN` value
- Trigger: ☑ Pipeline events
- Click **Add webhook**

**5d. Grant IAM Invoker access** to GitLab Duo's service account:
```bash
gcloud run services add-iam-policy-binding ops-orchestrator-gcp \
    --region us-central1 \
    --member="serviceAccount:gitlab-duo@YOUR-PROJECT.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

---

## Agent Commands

| Command | Action |
|---------|--------|
| `@ops-orchestrator` | Decompose issue into sprint tasks |
| `@ops-orchestrator-security` | Scan MR for vulnerabilities |
| `@ops-orchestrator-compliance` | Check MR policy gates |
| `@ops-orchestrator-estimate` | Estimate unweighted issues |
| `@ops-orchestrator-deps` | Map blockers |
| `@ops-orchestrator-deploy` | Deployment readiness report |

---

## Running Tests

```bash
pip install pytest pyyaml
python -m pytest tests/ -v
```

**183 tests** across 3 test files covering all agent logic (planning, deployment, standup, security, compliance, estimation, CI/CD).

---

## Anthropic Bonus Track

- Claude is the reasoning engine for all six agents
- Claude is accessed via **GitLab Duo AI Gateway** (GitLab's Anthropic integration)
- No hardcoded model strings anywhere in the codebase
- Model configured in GitLab UI only
- Every agent output includes attribution to Claude via Anthropic

---

## 🌱 Green Agent Design

Every OpsOrchestrator agent minimises token usage before
making any LLM call. Skip logic runs first — if the condition
is not met, no inference happens at all.

| Agent | Skip Condition | Tokens Saved |
|-------|---------------|--------------|
| Planning | Description < 30 words → stop | Full decomposition |
| Security | Docs/images/lock files → skip file | Per-file scan |
| Estimation | All issues already weighted → stop | Full analysis |
| Deployment | Non-protected branch → stop | Full evaluation |
| Standup | No open issues or MRs → stop | Full digest |

**Result:** ~$0.05 per full SDLC cycle.
All inference via GitLab Duo AI Gateway — zero direct API cost.

---

## ☁️ Google Cloud Integration

The OpsOrchestrator MCP server runs on **Google Cloud Run**
and provides two enterprise features:

**Compliance Audit Vault**
When the Compliance or Security Agent finishes a scan, it
calls the `archive_audit_report` MCP tool to stream the
structured JSON audit log into a GCS bucket for permanent,
tamper-proof storage.

**CI/CD AutoDoctor Webhook**
When a GitLab pipeline fails, it posts to `POST /webhook/gitlab`
on the Cloud Run server, which wakes up the DevOps Agent to
diagnose and fix the failure.

```
MCP Server: https://[your-cloud-run-url]/
Dashboard:  https://[your-cloud-run-url]/
Webhook:    POST https://[your-cloud-run-url]/webhook/gitlab
Audit:      gs://ops-orchestrator-compliance-vault/
```

See `mcp/app.py` and `mcp/mcp_config.json`.

---

## License

Apache 2.0 — see [LICENSE](LICENSE)
