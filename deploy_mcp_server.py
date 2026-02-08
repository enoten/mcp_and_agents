from fastmcp import FastMCP
import requests

mcp = FastMCP("My Server")


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

    api_url =  f"http://127.0.0.1:8001/rate/{base}/{target}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
            #print(response.__dict__)
            return response.json() 
    else:
            return {'data':None}


@mcp.tool()
def calculate_metrics(data: list[int]) -> dict:
    """Computes basic metrics for a list of numbers."""
    return {
        "sum": sum(data),
        "average": sum(data) / len(data),
        "count": len(data)
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)