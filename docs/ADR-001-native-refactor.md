# ADR-001: Native Refactor to GitLab Duo Platform

## Context
The previous version of the Planning Agent utilized a "Layer 2" architecture consisting of an external FastAPI backend deployed on Cloud Run, utilizing Firestore for state, and connecting directly to Anthropic's API via a hardcoded API key. This approach violates the premise of a GitLab-native agent and disqualifies the submission for the Anthropic Prize, adding unnecessary complexity.

## Decision
We decided to completely remove Layer 2 (`app/`, `infrastructure/`, `duo/`) and refactor all agent logic into pure YAML flows running natively on the **GitLab Duo Agent Platform**. 

## Component Replacement

| Deleted Component (Layer 2) | Replaced By (Layer 1) |
|-----------------------------|-----------------------|
| `app/` (FastAPI backend) | GitLab Duo native YAML flows |
| Cloud Run (`infrastructure/`) | GitLab Native Compute |
| Firestore (State) | GitLab Issues / MR Labels |
| Anthropic API Keys | GitLab Duo AI Gateway |
| `duo/antigravity_flow.yml` | `.gitlab/duo/planning_flow.yml` |

## Trade-offs
- **Pros:** Zero-infrastructure setup, single-click agent configuration, no API keys to leak, better compliance and maintainability.
- **Cons:** Less freedom to write custom arbitrary Python code; all executions must be constrained to what is supported by Duo Agent component inputs and the LLM's logical interpretation.

## Consequences
The setup is now trivial. The agent is entirely eligible for the Anthropic prize as it configures models securely via the UI and relies exclusively on Claude's integration with GitLab Duo. Over 90% of boilerplate code was removed.
