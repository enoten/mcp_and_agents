import asyncio
import os
import time
import jwt
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from dotenv import load_dotenv
load_dotenv()   

MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")#, "your-256-bit-secret-key-change-in-production")

#correct secret key for testing
#MCP_JWT_SECRET = MCP_JWT_SECRET[:-1] + "1"

MCP_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
#MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET", "your-256-bit-secret-key-change-in-production")
MCP_JWT_ALGORITHM = os.environ.get("MCP_JWT_ALGORITHM", "HS256")


def get_jwt_token() -> str:
    """Generate a JWT with standard claims (exp, iat)."""
    payload = {
        "sub": "mcp-client",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour
    }
    return jwt.encode(payload, MCP_JWT_SECRET, algorithm=MCP_JWT_ALGORITHM)


async def main():
    token = get_jwt_token()
    print(token)
    client = Client(MCP_URL, auth=BearerAuth(token))

    async with client:
        await client.ping()
        result = await client.call_tool("get_private_data", {})
        # Result may have .data (list of content items) or a string
        if hasattr(result, "data") and result.data:
            if isinstance(result.data, str):
                print(result.data)
            else:
                for part in result.data:
                    if hasattr(part, "text"):
                        print(part.text, end="")
                    else:
                        print(part, end="")
        else:
            print(result)


if __name__ == "__main__":
    asyncio.run(main())