"""MCP client for Sales SQLite server. JWT with context.username, calls get_my_clients."""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
from datetime import timedelta
from pathlib import Path
import sys

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8011/mcp")


def create_jwt(username: str) -> str:
    payload = {"context": {"username": username}, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    header = {"alg": "HS256", "typ": "JWT"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    msg = f"{h}.{p}".encode()
    sig = base64.urlsafe_b64encode(hmac.new(MCP_JWT_SECRET.encode(), msg, hashlib.sha256).digest()).rstrip(b"=").decode()
    return f"{h}.{p}.{sig}"


async def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "Alice Chen"
    #username = os.environ.get("SALES_USER", "Alice Chen")
    token = create_jwt(username)

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(
        MCP_SERVER_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=timedelta(seconds=30),
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_my_clients", arguments={"auth_token": token})
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        print(json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        print(content.text)
                else:
                    print(content)


if __name__ == "__main__":
    if not MCP_JWT_SECRET:
        raise SystemExit("MCP_JWT_SECRET must be set in .env")
    asyncio.run(main())
