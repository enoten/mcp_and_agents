# proxy_server.py
from fastmcp.server.server import create_proxy
import uvicorn
import os

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Example 1: Proxy a local script (Stdio -> SSE)
# This is useful for exposing a local Python script or CLI tool to the network.
# We assume you have a file named 'local_tools.py' that runs an MCP server.
LOCAL_TARGET = "python local_tools.py" 

# Example 2: Proxy a remote URL (HTTP -> SSE)
# This allows you to "re-broadcast" a remote server securely.
REMOTE_TARGET = "https://demo.mcp-server.com/sse"

# ---------------------------------------------------------
# CREATE PROXY
# ---------------------------------------------------------

# create_proxy automatically detects if the target is a command or a URL.
# It creates a full MCP server capable of handling SSE and HTTP.
mcp_proxy = create_proxy(
    LOCAL_TARGET, 
    name="MyGatewayProxy",
    # Optional: Debugging logs to see the traffic being forwarded
    debug=True 
)

# Expose the ASGI app for deployment
app = mcp_proxy.sse_app()

if __name__ == "__main__":
    # Run the server using uvicorn
    # This exposes the proxy at http://0.0.0.0:8000/sse
    uvicorn.run(app, host="0.0.0.0", port=8000)