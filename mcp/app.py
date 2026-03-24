import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from mcp.server.fastmcp import FastMCP
import uvicorn

app = FastAPI(title="OpsOrchestrator Backend")
mcp = FastMCP("ops-orchestrator-gcp")

# FIX-12: Consume MCP_ENV — set by deploy_to_gcp.sh as "production"
MCP_ENV = os.environ.get("MCP_ENV", "development")

# Warn on startup if required env vars are missing in production
if MCP_ENV == "production":
    missing = [v for v in ["GITLAB_PAT", "GITLAB_WEBHOOK_TOKEN"] if not os.environ.get(v)]
    if missing:
        print(json.dumps({
            "severity": "WARNING",
            "message": f"Missing env vars in production: {missing}. Webhook will not post comments."
        }))

# ── Authentication ────────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-Gitlab-Token", auto_error=False)

async def verify_token(api_key: str = Security(api_key_header)):
    expected_token = os.environ.get("GITLAB_WEBHOOK_TOKEN", "hackathon-dev-token")
    if api_key != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Gitlab-Token"
        )

# ── MCP Tools ─────────────────────────────────────────────────────────────────
@mcp.tool()
def health_check() -> str:
    """Returns the health status of the OpsOrchestrator MCP Server."""
    env_label = "production" if MCP_ENV == "production" else "development"
    return f"OpsOrchestrator MCP Server is healthy. Environment: {env_label}. Ready."


@mcp.tool()
def archive_audit_report(mr_iid: int, audit_data: str) -> str:
    """Vaults the compliance JSON audit report to GCP Cloud Logging."""
    print(json.dumps({
        "severity": "INFO",
        "audit_event": "COMPLIANCE_VAULT",
        "mr_iid": mr_iid,
        "data": audit_data
    }))
    return f"Successfully vaulted audit report for MR !{mr_iid} to GCP Logging."


# ── Webhook Endpoint ──────────────────────────────────────────────────────────
@app.post("/webhook/gitlab", dependencies=[Depends(verify_token)])
async def gitlab_webhook(request: Request):
    """
    Receives GitLab pipeline:failure events and dispatches the CI/CD AutoDoctor
    by posting a comment that triggers @ops-orchestrator-devops.
    """
    payload = await request.json()

    if payload.get("object_kind") != "pipeline":
        return {"status": "ignored", "reason": "not a pipeline event"}

    status_val = payload.get("object_attributes", {}).get("status")
    if status_val != "failed":
        return {"status": "ignored", "reason": f"pipeline status is {status_val}"}

    pipeline_id = payload.get("object_attributes", {}).get("id")
    project_id = payload.get("project", {}).get("id")
    print(f"Triggering CI/CD AutoDoctor for pipeline {pipeline_id} on project {project_id}")

    pat = os.environ.get("GITLAB_PAT")
    if pat and project_id:
        triage_iid = os.environ.get("DEVOPS_TRIAGE_ISSUE_IID", "1")
        async with httpx.AsyncClient() as client:
            # FIX-N4: Check response status — a 404 means the triage issue IID is wrong
            response = await client.post(
                f"https://gitlab.com/api/v4/projects/{project_id}/issues/{triage_iid}/notes",
                headers={"PRIVATE-TOKEN": pat},
                json={"body": f"@ops-orchestrator-devops Pipeline {pipeline_id} failed. Please diagnose."},
                timeout=10.0,
            )
            if response.status_code not in (200, 201):
                error_detail = response.text[:200]
                print(json.dumps({
                    "severity": "ERROR",
                    "message": f"GitLab API returned {response.status_code} posting to issue #{triage_iid}",
                    "detail": error_detail,
                    "project_id": project_id,
                    "triage_iid": triage_iid,
                }))
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"GitLab API error {response.status_code} posting to issue #{triage_iid}. "
                           f"Check DEVOPS_TRIAGE_ISSUE_IID env var. Detail: {error_detail}"
                )

    return {"status": "triggered", "pipeline_id": pipeline_id}


# ── Mount MCP SSE transport (mcp>=1.1.0 API: sse_app()) ──────────────────────
app.mount("/sse", mcp.sse_app())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(json.dumps({
        "severity": "INFO",
        "message": "OpsOrchestrator MCP Server starting",
        "environment": MCP_ENV,
        "port": port
    }))
    uvicorn.run(app, host="0.0.0.0", port=port)