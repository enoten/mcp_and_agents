import os
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "my-secret-token")
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8000"))


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization")

        if not auth_header or auth_header != f"Bearer {BEARER_TOKEN}":
            raise ToolError("Unauthorized: Invalid or missing API key")

        return await call_next(context)


mcp = FastMCP("SecureServer")
mcp.add_middleware(AuthMiddleware())


@mcp.tool()
def get_private_data() -> str:
    return "This is protected data."


if __name__ == "__main__":
    mcp.run(transport="http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)