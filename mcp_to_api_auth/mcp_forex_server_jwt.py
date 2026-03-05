"""
MCP Forex Server that calls the JWT-protected FastAPI currency rate API.

- MCP tool calls require Bearer JWT (MCP_JWT_SECRET)
- Outbound API calls use Bearer JWT (FAPI_JWT_SECRET)
"""
import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
import requests

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
FAPI_JWT_SECRET = os.environ.get("FAPI_JWT_SECRET")
MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")


def _base64url_decode(s: str) -> bytes:
    """Decode base64url string to bytes."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _verify_mcp_jwt(token: str) -> dict:
    """Verify HS256 JWT for MCP client auth. Raises ValueError if invalid."""
    if not MCP_JWT_SECRET:
        raise ValueError("MCP_JWT_SECRET not configured")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    header_b64, payload_b64, sig_b64 = parts
    message = f"{header_b64}.{payload_b64}".encode()
    secret_bytes = MCP_JWT_SECRET.encode() if isinstance(MCP_JWT_SECRET, str) else MCP_JWT_SECRET
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret_bytes, message, hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(sig_b64, expected_sig):
        raise ValueError("Invalid signature")
    payload_json = _base64url_decode(payload_b64).decode("utf-8")
    payload = json.loads(payload_json)
    exp = payload.get("exp")
    if exp is not None and exp < int(time.time()):
        raise ValueError("Token expired")
    return payload


class MCPAuthMiddleware(Middleware):
    """Require Bearer JWT for MCP tool calls."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization")

        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise ToolError("Unauthorized: Missing or invalid Authorization header")

        token = auth_header[7:].strip()
        try:
            _verify_mcp_jwt(token)
        except ValueError as e:
            raise ToolError(f"Unauthorized: {e}") from e
        return await call_next(context)


def _create_jwt_token() -> str:
    """Create HS256 JWT for API auth (stdlib only, no PyJWT)."""
    if not FAPI_JWT_SECRET:
        raise ValueError("FAPI_JWT_SECRET must be set in .env")
    payload = {
        "sub": "mcp-forex-server",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}".encode()
    secret_bytes = FAPI_JWT_SECRET.encode() if isinstance(FAPI_JWT_SECRET, str) else FAPI_JWT_SECRET
    sig = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


mcp = FastMCP("Forex MCP Server")
mcp.add_middleware(MCPAuthMiddleware())


@mcp.tool()
def cross_currency_rate(base: str, target: str):
    """
    Fetches the current exchange rate between two currencies from the JWT-protected API.

    Requires: Authorization: Bearer <JWT> header (signed with MCP_JWT_SECRET).

    Args:
        base: The base currency (e.g., "USD", "SGD").
        target: The target currency (e.g., "GBP", "JPY").

    Returns:
        The exchange rate info: {"base", "target", "rate"}, or {"error": ...} on failure.
    """
    token = _create_jwt_token()
    url = f"{API_BASE_URL.rstrip('/')}/rate/{base.upper()}/{target.upper()}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, 
                                headers=headers, 
                                timeout=10,
                                verify=False)
        if response.status_code == 200:
            return response.json()
        return {"error": response.text or f"HTTP {response.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    if not MCP_JWT_SECRET:
        raise SystemExit("MCP_JWT_SECRET must be set in .env for MCP auth")
    if not FAPI_JWT_SECRET:
        raise SystemExit("FAPI_JWT_SECRET must be set in .env for API auth")
    mcp.run(transport="http", 
            host="0.0.0.0", 
            port=8001)