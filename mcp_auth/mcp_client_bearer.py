import asyncio
import os
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

MCP_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "my-secret-token")


async def main():
    client = Client(MCP_URL, auth=BearerAuth(BEARER_TOKEN))

    async with client:
        await client.ping()
        result = await client.call_tool("get_private_data", {})
        # Result may have .data (list of content items) or .content
        if hasattr(result, "data") and result.data:
            for part in result.data:
                if hasattr(part, "text"):
                    print(part.text)
                else:
                    print(part)
        else:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())