"""
MCP Server for SQLite sales.db with JWT authentication.

- All tool calls require Bearer JWT
- JWT payload must contain: {"context": {"username": "<sales_person_name>"}}
- Tool get_my_clients queries sales.db and returns that salesperson's clients
"""
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

DB_PATH = Path(__file__).parent / "sales.db"
MCP_JWT_SECRET = os.environ.get("MCP_JWT_SECRET")


def _base64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _verify_jwt_and_get_username(token: str) -> str:
    """Verify HS256 JWT and extract context.username. Raises ValueError if invalid."""
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
    context = payload.get("context") or {}
    username = context.get("username")
    if not username:
        raise ValueError("JWT context must contain username")
    return str(username).strip()


def _get_token_from_headers() -> str:
    headers = get_http_headers()
    if not headers:
        raise ToolError("Unauthorized: No HTTP headers available")
    auth_header = headers.get("authorization") or headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise ToolError("Unauthorized: Missing Authorization header")
    return auth_header[7:].strip()


class JwtAuthMiddleware(Middleware):
    """Require Bearer JWT for tool calls. Fallback: tool can receive auth_token argument."""

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        try:
            token = _get_token_from_headers()
        except ToolError:
            return await call_next(context)
        try:
            _verify_jwt_and_get_username(token)
        except ValueError as e:
            raise ToolError(f"Unauthorized: {e}") from e
        return await call_next(context)


def _query_clients(sales_person_name: str) -> list[dict]:
    """Query sales.db for clients of the given salesperson."""
    if not DB_PATH.exists():
        return [{"error": f"Database not found: {DB_PATH}"}]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT sales_person_name, associate_client_name FROM sales_clients WHERE sales_person_name = ?",
            (sales_person_name,),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


mcp = FastMCP("Sales SQLite MCP Server")
mcp.add_middleware(JwtAuthMiddleware())


@mcp.tool()
def get_my_clients(auth_token: str = "") -> list[dict]:
    """
    Get clients for the authenticated salesperson.

    Username is taken from JWT context.username. Provide JWT via Authorization header
    or auth_token argument. JWT payload: {"context": {"username": "<name>"}}.

    Returns:
        List of {sales_person_name, associate_client_name}.
    """
    token = auth_token.strip() if auth_token else None
    if not token:
        try:
            token = _get_token_from_headers()
        except ToolError:
            raise ToolError(
                "Unauthorized: Provide JWT via Authorization: Bearer header or auth_token argument."
            ) from None
    username = _verify_jwt_and_get_username(token)
    return _query_clients(username)


if __name__ == "__main__":
    if not MCP_JWT_SECRET:
        raise SystemExit("MCP_JWT_SECRET must be set in .env")
    if not DB_PATH.exists():
        print("sales.db not found. Run init_sqlite_db.py first.")
    mcp.run(transport="http", host="0.0.0.0", port=8011)
