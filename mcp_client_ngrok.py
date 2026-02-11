from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import asyncio

#direct mcp call
mcp_url="http://localhost:8001/mcp"

#proxy mcp call
proxy_url="http://localhost:8003/mcp"

ngrok_url="https://nonrepresentational-anne-tantalizingly.ngrok-free.dev"


async def main():
    transport = StreamableHttpTransport(
    #url="http://localhost:8000/mcp",
    url=ngrok_url,
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
        #tools_dict = {t.name: t.description for t in tools}
        #print(f"Server Tools: {tools_dict} \n")

        tools_list = [t.name for t in tools]
        print(f"Server Tools: {tools_list} \n")

        # 4. Call a specific tool
        # Arguments are passed as a dictionary
        #result = await client.call_tool("get_weather", {"city": "washingtondc"})
        #print(f"Result: {result} \n")

        # 5. Call a cross_currecny_tool
        # Arguments are passed as a dictionary
        #result = await client.call_tool("cross_currency_rate", {"base": "USD", "target": "GBP"})
        result = await client.call_tool('forex_api_cross_currency_rate', {"base": "USD", "target": "GBP"})
        print(f"Raw Result: {result} \n")

        print(f"Result's Structured Content: {result.structured_content} \n")
        print()



if __name__ == "__main__":
    asyncio.run(main())