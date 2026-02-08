from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import asyncio


async def main():
    transport = StreamableHttpTransport(
    url="http://localhost:8000/mcp",
    # headers={
    #     "Authorization": "Bearer your-token-here",
    #     "X-Custom-Header": "value"
    # }
    )

    client = Client(transport)

    async with client:
        # 3. Discover capabilities
        tools = await client.list_tools()
        #print(tools[0].__dict__)
        tools_dict = {t.name: t.description for t in tools}
        print(f"Server Tools: {tools_dict} \n")

        # 4. Call a specific tool
        # Arguments are passed as a dictionary
        #result = await client.call_tool("get_weather", {"city": "washingtondc"})
        #print(f"Result: {result} \n")

        # 5. Call a cross_currecny_tool
        # Arguments are passed as a dictionary
        result = await client.call_tool("cross_currency_rate", {"base": "USD", "target": "GBP"})
        print(f"Raw Result: {result} \n")

        print(f"Result's Structured Content: {result.structured_content} \n")
        print()



if __name__ == "__main__":
    asyncio.run(main())