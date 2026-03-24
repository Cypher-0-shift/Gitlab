# CHANGELOG

All notable changes to OpsOrchestrator will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] — 2026-03-24

### Added
- `dependency_flow.yml` — new Dependency Agent scans for outdated packages and opens upgrade MRs
- `agents/ops_orchestrator.md` — chat agent setup guide
- `.dockerignore` — prevents tests/, docs/, flows/ from entering the Cloud Run image
- `CHANGELOG.md` — this file
- `docs/ADR-001-native-refactor.md` — architecture decision record for native refactor
- Bidirectional sync check in `.gitlab-ci.yml` (flows/ ↔ .gitlab/duo/)
- MCP server authentication via `X-Gitlab-Token` header
- `health_check` MCP tool for Cloud Run liveness probing

### Fixed
- `planning_flow.yml` Phase 8: `create_commit` now runs before `create_merge_request` to bootstrap branch
- `standup_flow.yml` Phase 0: dedicated "Daily Standup Digest" issue search/create instead of random first issue
- `deployment_flow.yml` Signals 1–2: replaced hallucinated `list_pipelines`/`get_project_jobs` with `get_pipeline_errors`/`get_pipeline_failing_jobs`
- `estimation_flow.yml`: timeout increased from 180s to 300s; weight=0 issues explicitly skipped
- `requirements.txt`: added `fastapi`, `uvicorn`, `httpx`, `mcp[cli]` with version pins
- License unified as Apache 2.0 (was MIT in file, Apache 2.0 in badge)
- All test paths corrected to use relative paths — no more sandbox-absolute paths

### Changed
- MCP server name: `planning-agent-gcp-mcp` → `ops-orchestrator-gcp`
- CI job renamed: `test_standup_logic` → `test_all_agents`
- `deploy_to_gcp.sh`: added `--no-allow-unauthenticated`; env vars now include GITLAB_PAT
- `mcp/mcp_config.json` and `.gitlab/duo/mcp.json`: hardcoded GCP project number replaced with `YOUR_CLOUD_RUN_URL` placeholder

### Removed
- `list_vulnerabilities` from `security_flow.yml` toolset (dead tool — never called)
- `run_glql_query` from `standup_flow.yml` toolset (dead tool — never called)
- `archive_audit_report` from `compliance_flow.yml` toolset (MCP tool, not native)

---

## [1.0.0] — 2026-03-21

### Added
- Initial hackathon submission
- 8 specialist YAML flows: planning, security, compliance, deployment, estimation, devops, standup, intent_router
- `agent.yaml` hub agent with routing rules
- GCP Cloud Run MCP server (`mcp/app.py`) with `archive_audit_report` tool
- 183-test suite across 3 test files
- `.gitlab-ci.yml` with YAML validation and test stages
- `.ai-catalog-mapping.json` with catalog registration metadata
- `docs/architecture.md` system architecture document
- Apache 2.0 license
