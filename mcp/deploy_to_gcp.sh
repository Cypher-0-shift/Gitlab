#!/bin/bash
# Deployment script for Google Cloud Run
# Ensure you are authenticated with `gcloud auth login` and `gcloud config set project YOUR_PROJECT_ID`

echo "Deploying Planning Agent MCP Server to Google Cloud Run..."

gcloud run deploy planning-agent-mcp \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --set-env-vars="MCP_ENV=production"

echo "Deployment complete! Add your Cloud Run URL to your mcp_config.json if connecting remotely."
