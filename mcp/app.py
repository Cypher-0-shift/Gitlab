from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP Server for Google Cloud Run
mcp = FastMCP("planning-agent-gcp-mcp")

@mcp.tool()
def health_check() -> str:
    """Returns the health status of the Planning Agent GCP MCP Server."""
    return "GCP Cloud Run MCP Server is healthy and running!"

@mcp.tool()
def get_agent_capabilities() -> dict:
    """Returns the capabilities of the Planning Agent MCP server."""
    return {
        "flows": ["planning", "security", "compliance", "estimation", "deployment", "dependency"],
        "platform": "GitLab Duo",
        "cloud": "Google Cloud Run"
    }

if __name__ == "__main__":
    # Default to 8080 for Cloud Run
    port = int(os.environ.get("PORT", 8080))
    host = "0.0.0.0"
    
    print(f"Starting MCP Server on {host}:{port} with SSE transport...")
    mcp.settings.port = port
    mcp.settings.host = host
    
    # Run with Server-Sent Events (SSE) which is ideal for HTTP deployments like Cloud Run
    mcp.run(transport="sse")
