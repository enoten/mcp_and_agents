import os
import jwt
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from dotenv import load_dotenv
load_dotenv()   

MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")#, "your-256-bit-secret-key-change-in-production")
MCP_JWT_ALGORITHM = os.environ.get("MCP_JWT_ALGORITHM", "HS256")
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8000"))


class AuthMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization")

        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise ToolError("Unauthorized: Missing or invalid Authorization header")

        token = auth_header[7:].strip()  # Remove "Bearer " prefix

        try:
            jwt.decode(token, MCP_JWT_SECRET, algorithms=[MCP_JWT_ALGORITHM])
        except jwt.InvalidTokenError as e:
            raise ToolError(f"Unauthorized: Invalid or expired token: {e}") from e

        return await call_next(context)


mcp = FastMCP("SecureServer")
mcp.add_middleware(AuthMiddleware())


@mcp.tool()
def get_private_data() -> str:
    """Get protected data."""
    return "This is protected data."


if __name__ == "__main__":
    mcp.run(transport="http", 
            host=MCP_SERVER_HOST, 
            port=MCP_SERVER_PORT)