# Planning Agent Architecture

The Planning Agent leverages a fully GitLab-native architecture, operating entirely within the GitLab Duo Agent Platform. There is no external infrastructure, no external API keys, and no persistent state outside of GitLab. The AI reasoning engine (Claude via Anthropic) is queried through the GitLab Duo AI Gateway.

## Architecture Diagram
```
GitLab UI/Events
       |
     (Web)
       V
+------------------------------------------+
|          Ops Orchestrator Agent          |
|        (agents/ops_orchestrator)         |
+------------------------------------------+
       | Routes based on event type
       +--> Planning Flow (planning_flow.yml)
       +--> Security Flow (security_flow.yml)
       +--> Compliance Flow (compliance_flow.yml)
       +--> Estimation Flow (estimation_flow.yml)
       +--> Dependency Flow (dependency_flow.yml)
       +--> Deployment Flow (deployment_flow.yml)
       
       V
  [GitLab Duo AI Gateway] -> [Claude Model]
```

## Component Map

| Component | Responsibility |
|-----------|----------------|
| `ops_orchestrator/agent.yaml` | Routes events to specific flows |
| `planning_flow.yml` | Decomposes issues to tasks |
| `security_flow.yml` | Scans MR diffs |
| `compliance_flow.yml` | Checks MR policy gates |
| `estimation_flow.yml` | Estimates issue points |
| `dependency_flow.yml` | Maps blocker issues |
| `deployment_flow.yml` | Deployment readiness report |

## File Structure
```
planning-ai-agent/
├── .gitlab/
│   ├── duo/
│   │   ├── planning_flow.yml      ★ Core planning agent
│   │   ├── security_flow.yml
│   │   ├── compliance_flow.yml
│   │   ├── estimation_flow.yml
│   │   ├── dependency_flow.yml
│   │   └── deployment_flow.yml
│   ├── compliance_policy.yaml
│   └── ai_config.yaml
├── agents/
│   ├── planning_agent.md
│   └── ops_orchestrator/
│       └── agent.yaml
├── tests/
│   ├── test_flows.py              56 unit tests
│   └── test_deployment_flow.py   59 unit tests
├── docs/
│   ├── architecture.md
│   └── ADR-001-native-refactor.md
├── .gitlab-ci.yml
├── requirements-dev.txt
├── LICENSE
└── README.md
```

## Event-to-Agent Routing

| Event | Condition | Delegated Flow |
|-------|-----------|----------------|
| `issue_created` | desc >= 30 words | `planning_flow` |
| `merge_request_opened` | always | `security_flow` |
| `merge_request_approved` | always | `compliance_flow` |
| `pipeline_success` | protect branch | `deployment_flow` |
| `pipeline_failed` | protect branch | `deployment_flow` |

## Technology Stack

| Technology | Purpose |
|------------|---------|
| GitLab Duo | Agent Platform execution |
| YAML | Flow definitions |
| Python (`unittest`) | Flow validation |

## Running Tests
Run `python3 -m unittest discover -s tests -v` to execute all logic verification tests natively. No extra dependencies needed.
