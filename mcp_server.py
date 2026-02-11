from fastmcp import FastMCP
import requests

mcp = FastMCP("Weather MCP Server")


@mcp.tool()
async def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Example using a placeholder API or actual weather API
    api_url =  f"https://wttr.in/{city}?format=3"
    
    response = requests.get(api_url)
    if response.status_code == 200:
            #print(response.__dict__)
            return response.json() 
    else:
            return {'data':None}

if __name__ == "__main__":
    mcp.run(transport="http", 
            host="0.0.0.0", 
            port=8002)