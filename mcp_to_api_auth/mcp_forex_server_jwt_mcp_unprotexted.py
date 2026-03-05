"""
MCP Forex Server that calls the JWT-protected FastAPI currency rate API.

API: GET /rate/{base_currency}/{target_currency}
Auth: Bearer JWT (FAPI_JWT_SECRET)
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
import requests

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
JWT_SECRET = os.environ.get("FAPI_JWT_SECRET")


def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _create_jwt_token() -> str:
    """Create HS256 JWT for API auth (stdlib only, no PyJWT)."""
    if not JWT_SECRET:
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
    secret_bytes = JWT_SECRET.encode() if isinstance(JWT_SECRET, str) else JWT_SECRET
    sig = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


mcp = FastMCP("Forex MCP Server")


@mcp.tool()
def cross_currency_rate(base: str, target: str):
    """
    Fetches the current exchange rate between two currencies from the JWT-protected API.

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
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": response.text or f"HTTP {response.status_code}"}
    except requests.RequestException as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)