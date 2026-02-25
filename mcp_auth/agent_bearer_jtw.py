import os
import time
import base64
import hashlib
import hmac
import json
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp")
MCP_JWT_SECRET = os.environ["MCP_JWT_SECRET"]
MCP_JWT_ALGORITHM = os.environ.get("MCP_JWT_ALGORITHM", "HS256")

def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _create_hs256_jwt(payload: dict, secret: str) -> str:
    """Create HS256 JWT using stdlib only (no PyJWT dependency)."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}".encode()
    secret_bytes = secret.encode() if isinstance(secret, str) else secret
    signature = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def get_jwt_token() -> str:
    """Generate a JWT with standard claims for MCP server authentication."""
    if not MCP_JWT_SECRET:
        raise ValueError(
            "MCP_JWT_SECRET must be set in environment. "
            "Add it to mcp_auth/.env or set the env var."
        )
    payload = {
        "sub": "strands-agent",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    if MCP_JWT_ALGORITHM.upper() != "HS256":
        raise ValueError("Only HS256 is supported without PyJWT. Install PyJWT for other algorithms.")
    return _create_hs256_jwt(payload, MCP_JWT_SECRET)


# Generate JWT for MCP connection (must match server's MCP_JWT_SECRET)
token = get_jwt_token()

mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        headers={"Authorization": f"Bearer {token}"},
    ),
    tool_filter=["get_private_data"],
)

root_agent = Agent(
    name="bearer_jwt_agent",
    model="gemini-2.0-flash",
    description="Agent that fetches protected data from the JWT-authenticated MCP server.",
    instruction="""
    You help users access protected data. Use the get_private_data tool when asked
    for private, protected, or secure data.
    """,
    tools=[mcp_toolset],
)
