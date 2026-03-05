"""
AWS Strands Agent that calls get_private_data tool from the JWT-authenticated MCP server
defined in mcp_server_bearer_token_jwt.py.
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Load .env from mcp_auth directory (and project root as fallback)
#_env_dir = Path(__file__).parent
#load_dotenv(_env_dir / ".env")
load_dotenv()  # Also load from cwd

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8001/mcp")
MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")
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


def create_mcp_client():
    """Create streamable HTTP client with Bearer JWT authorization."""
    token = get_jwt_token()
    return streamablehttp_client(
        MCP_SERVER_URL,
        headers={"Authorization": f"Bearer {token}"},
    )


# Increase startup_timeout if server is slow; default 30s may be too short
streamable_http_mcp_client = MCPClient(
    create_mcp_client,
    startup_timeout=60,
)

if __name__ == "__main__":
    # Pre-flight checks
    if not MCP_JWT_SECRET:
        print("ERROR: MCP_JWT_SECRET not set. Add to mcp_auth/.env", file=sys.stderr)
        sys.exit(1)
    #print(f"Connecting to MCP server at {MCP_SERVER_URL}")
    #print("Ensure the server is running: python mcp_server_bearer_token_jwt.py")

    if len(sys.argv) >= 1:
        query = sys.argv[1]

    try:
        with streamable_http_mcp_client:
            tools = streamable_http_mcp_client.list_tools_sync()
            agent = Agent(tools=tools)

            # Call get_private_data via natural language (agent will select the tool)
            if query:
                response = agent(query)
            response = agent("Get the private data for me.")
            print(response)
    except Exception as e:
        print(f"\nMCPClientInitializationError / connection failed: {e}", file=sys.stderr)
        print("\nTroubleshooting:", file=sys.stderr)
        print("  1. Start the MCP server: cd mcp_auth && python mcp_server_bearer_token_jwt.py", file=sys.stderr)
        print("  2. Verify MCP_SERVER_URL matches server (default http://localhost:8000/mcp)", file=sys.stderr)
        print("  3. Ensure MCP_JWT_SECRET in .env matches the server", file=sys.stderr)
        sys.exit(1)
