from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import asyncio

#direct mcp call
mcp_url="http://localhost:8001/mcp"

#proxy mcp call
proxy_url="http://localhost:8003/mcp"


async def main():
    transport = StreamableHttpTransport(
    url=proxy_url,
    )

    client = Client(transport)

    async with client:
        # 1. Discover capabilities
        tools = await client.list_tools()
        #print(tools[0].__dict__)
        #tools_dict = {t.name: t.description for t in tools}
        #print(f"Server Tools: {tools_dict} \n")

        tools_list = [t.name for t in tools]
        print(f"Server Tools: {tools_list} \n")

        # 2. Call a cross_currecny_tool
        # Arguments are passed as a dictionary
        #result = await client.call_tool("cross_currency_rate", {"base": "USD", "target": "GBP"})
        result = await client.call_tool('forex_api_cross_currency_rate', {"base": "USD", "target": "GBP"})
        print(f"Raw Result: {result} \n")

        print(f"Result's Structured Content: {result.structured_content} \n")
        print()

if __name__ == "__main__":
    asyncio.run(main())