# OpsOrchestrator — Chat Agent Setup Guide

This guide explains how to configure the OpsOrchestrator Hub Agent in GitLab Duo.
The Hub Agent uses `agents/agent.yaml` as its configuration.

## Prerequisites
- GitLab Duo Agent Platform enabled on your group or project
- At least one OpsOrchestrator flow enabled (see README Setup Steps 1–2)

## Setup

### 1. Create the Agent
Go to **GitLab → Automate → Agents → New agent**

- **Name:** `OpsOrchestrator`
- **Visibility:** Public
- **System prompt:** Copy the `system_prompt` field from `agents/agent.yaml`

### 2. Enable Tools
In the agent configuration, enable the following tools:
- `get_issue`, `list_issues`, `create_issue`, `create_issue_note`
- `get_project_members`, `create_merge_request`, `get_merge_request`
- `list_merge_request_diffs`, `create_merge_request_note`
- `update_merge_request`, `update_issue`, `list_repository_tree`

### 3. Trigger the Agent
Post `@OpsOrchestrator` in any issue or MR comment to route your request
to the correct specialist agent.

## Commands Quick Reference

| Command | Use In | Action |
|---------|--------|--------|
| `@ops-orchestrator` | Issue comment | Sprint planning |
| `@ops-orchestrator-security` | MR comment | Security scan |
| `@ops-orchestrator-compliance` | MR comment | Compliance gates |
| `@ops-orchestrator-deploy` | MR comment | Deployment readiness |
| `@ops-orchestrator-estimate` | Issue comment | Story point estimation |
| `@ops-orchestrator-standup` | Any comment | Daily digest (also auto-runs at 09:00 UTC Mon–Fri if scheduled triggers are enabled) |
| `@ops-orchestrator-deps` | Issue comment | Dependency scan |
| `@ops-orchestrator-devops` | MR or issue | CI/CD AutoDoctor |

*Powered by OpsOrchestrator on GitLab Duo · Claude via Anthropic*
