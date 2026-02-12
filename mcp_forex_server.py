from fastmcp import FastMCP
import requests

mcp = FastMCP("Forex MCP Server")

@mcp.tool
def cross_currency_rate(base: str,
                target: str
                #api_key: str
                ):
    """
    Fetches the current exchange rate between two currencies.

    Args:
            base: The base currency (e.g., "SGD").
            target: The target currency (e.g., "JPY").

    Returns:
            The exchange rate information as a json response,
            or None if the rate could not be fetched.
    """

    api_url =  f"http://127.0.0.1:8000/rate/{base}/{target}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
            #print(response.__dict__)
            return response.json() 
    else:
            return {'data':None}


if __name__ == "__main__":
    mcp.run(transport="http", 
            host="0.0.0.0", 
            port=8001)