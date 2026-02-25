"""
MCP Gateway - API Gateway for Model Context Protocol.

Similar to an API gateway but for MCP: routes requests to backend MCP servers,
with authentication, rate limiting, logging, and health checks.
"""
import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

LOG = logging.getLogger("mcp_gateway")
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Gateway config from env
GATEWAY_HOST = os.environ.get("GATEWAY_HOST", "0.0.0.0")
GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", "8090"))
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY")  # Optional: require X-API-Key
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW_SEC = int(os.environ.get("RATE_LIMIT_WINDOW_SEC", "60"))
CONFIG_PATH = os.environ.get("GATEWAY_CONFIG", str(Path(__file__).parent / "gateway_config.json"))


def load_gateway_config() -> dict:
    """Load backend MCP servers from config file."""
    path = Path(CONFIG_PATH)
    if not path.exists():
        LOG.warning("Config %s not found, using default backends", CONFIG_PATH)
        return {
            "mcpServers": {
                "forex_api": {"url": "http://localhost:8001/mcp", "transport": "http"},
                "weather_forecast": {"url": "http://localhost:8002/mcp", "transport": "http"},
            }
        }
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- Middleware: Logging ---
class GatewayLoggingMiddleware(Middleware):
    """Log all MCP requests and responses."""

    async def on_message(self, context: MiddlewareContext, call_next):
        start = time.perf_counter()
        method = getattr(context, "method", "unknown")
        LOG.info("MCP request: %s", method)
        try:
            result = await call_next(context)
            elapsed_ms = (time.perf_counter() - start) * 1000
            LOG.info("MCP %s completed in %.1fms", method, elapsed_ms)
            return result
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            LOG.exception("MCP %s failed after %.1fms: %s", method, elapsed_ms, e)
            raise


# --- Middleware: API Key Auth (optional) ---
class ApiKeyAuthMiddleware(Middleware):
    """Require X-API-Key header if GATEWAY_API_KEY is set."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GATEWAY_API_KEY

    async def on_request(self, context: MiddlewareContext, call_next):
        if not self.api_key:
            return await call_next(context)
        try:
            from fastmcp.server.dependencies import get_http_headers
            headers = get_http_headers()
            key = headers.get("x-api-key") or headers.get("authorization", "").replace("Bearer ", "")
            if key != self.api_key:
                raise ToolError("Unauthorized: Invalid or missing API key")
        except ImportError:
            pass  # Non-HTTP transport
        return await call_next(context)


# --- Middleware: Rate Limiting ---
class RateLimitMiddleware(Middleware):
    """Simple in-memory rate limiter per client."""

    def __init__(self, requests_per_window: int = RATE_LIMIT_REQUESTS, window_sec: float = RATE_LIMIT_WINDOW_SEC):
        self.requests_per_window = requests_per_window
        self.window_sec = window_sec
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _client_id(self, context: MiddlewareContext) -> str:
        try:
            from fastmcp.server.dependencies import get_http_headers, get_http_request
            req = get_http_request()
            if req and hasattr(req, "client") and req.client:
                return req.client.host or "unknown"
            headers = get_http_headers()
            return headers.get("x-forwarded-for", "unknown").split(",")[0].strip()
        except Exception:
            return "default"

    async def on_request(self, context: MiddlewareContext, call_next):
        client = self._client_id(context)
        now = time.time()
        cutoff = now - self.window_sec
        self._requests[client] = [t for t in self._requests[client] if t > cutoff]
        if len(self._requests[client]) >= self.requests_per_window:
            raise ToolError(
                f"Rate limit exceeded: {self.requests_per_window} requests per {self.window_sec}s"
            )
        self._requests[client].append(now)
        return await call_next(context)


# --- Build Gateway ---
config = load_gateway_config()

# Parent gateway server: middleware + custom routes
gateway = FastMCP("MCP Gateway", description="API Gateway for MCP - routes to backend servers")

# Add gateway middleware (order: first added = first executed on request)
gateway.add_middleware(GatewayLoggingMiddleware())
if GATEWAY_API_KEY:
    gateway.add_middleware(ApiKeyAuthMiddleware())
gateway.add_middleware(RateLimitMiddleware())

# Mount proxy to backend MCP servers (all tools/resources from backends)
backend_proxy = FastMCP.as_proxy(config, name="MCP Gateway Proxy")
gateway.mount(backend_proxy)

# Custom health route
@gateway.custom_route("/health", methods=["GET"])
async def health():
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "ok",
        "service": "mcp-gateway",
        "backends": list(config.get("mcpServers", {}).keys()),
    })


if __name__ == "__main__":
    LOG.info("Starting MCP Gateway on %s:%s", GATEWAY_HOST, GATEWAY_PORT)
    LOG.info("Backends: %s", list(config.get("mcpServers", {}).keys()))
    gateway.run(transport="http", host=GATEWAY_HOST, port=GATEWAY_PORT)
