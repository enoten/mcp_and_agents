from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

backend = ProxyClient("http://localhost:8001/mcp",
                       sampling_handler=None)

remote_proxy = FastMCP.as_proxy(
    backend,
    name="Proxy Server"
)

# Run locally via stdio for Claude Desktop
if __name__ == "__main__":
    remote_proxy.run(
        transport="http", 
        host="0.0.0.0", 
        port=8003)  # Defaults to stdio transport