from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

# Define your backend servers
config = {
    "mcpServers": {        
        "forex_api": {
            "url": "http://localhost:8001/mcp",
            "transport": "http"
        },
        "weather_forecast": {
            "url": "http://localhost:8002/mcp",
            "transport": "http"
        },
        "search_fastmcp_docs": {
            "url": "https://gofastmcp.com/mcp",
            "transport": "http"
        }        
     }
}

remote_proxy = FastMCP.as_proxy(
    config,
    name="Proxy Server for Forex & Weather MCP Servers"
)

if __name__ == "__main__":
    remote_proxy.run(
        transport="http", 
        host="0.0.0.0", 
        port=8003) 