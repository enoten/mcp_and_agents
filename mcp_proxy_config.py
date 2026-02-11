from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

backend = ProxyClient("http://localhost:8001/mcp",
                       sampling_handler=None)

# Define your backend servers
config = {
    "mcpServers": {        
        "forex_api": {
            "url": "http://localhost:8001/mcp",
            "transport": "http"
        },
        "weather_api": {
            "url": "http://localhost:8002/mcp",
            "transport": "http"
        },
        "llm_sampling_api": {
            "url": "http://localhost:8007/mcp",
            "transport": "http"
        },
    }
}

remote_proxy = FastMCP.as_proxy(
    config,
    name="Proxy Server"
)

if __name__ == "__main__":
    remote_proxy.run(
        transport="http", 
        host="0.0.0.0", 
        port=8003) 