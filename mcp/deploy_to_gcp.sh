#!/bin/bash
set -e

# Required: Set these before running
: "${GITLAB_PAT:?GITLAB_PAT must be set — GitLab PAT with api scope}"
: "${GITLAB_WEBHOOK_TOKEN:?GITLAB_WEBHOOK_TOKEN must be set — secret token for webhook validation}"
: "${DEVOPS_TRIAGE_ISSUE_IID:=1}"  # Default to issue #1 if not set

echo "Deploying OpsOrchestrator Backend to Google Cloud Run..."
gcloud run deploy ops-orchestrator-gcp \
    --source . \
    --region us-central1 \
    --no-allow-unauthenticated \
    --port 8080 \
    --set-env-vars="MCP_ENV=production,GITLAB_PAT=${GITLAB_PAT},GITLAB_WEBHOOK_TOKEN=${GITLAB_WEBHOOK_TOKEN},DEVOPS_TRIAGE_ISSUE_IID=${DEVOPS_TRIAGE_ISSUE_IID}"

echo "Deployment complete!"
echo "Service URL: $(gcloud run services describe ops-orchestrator-gcp --region us-central1 --format 'value(status.url)')"
echo ""
echo "NEXT STEPS:"
echo "1. Update .gitlab/duo/mcp.json with the Service URL above"
echo "2. Configure GitLab Webhook at: Project → Settings → Webhooks"
echo "   URL: <service-url>/webhook/gitlab"
echo "   Secret: your GITLAB_WEBHOOK_TOKEN"
echo "   Trigger: Pipeline events"
echo "3. Grant IAM Invoker role to GitLab Duo service account"
