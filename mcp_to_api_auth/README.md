# MCP to API Auth

End-to-end JWT authentication for MCP (Model Context Protocol) servers that call protected REST APIs. Demonstrates token generation, forwarding, and validation across MCP and HTTP layers.

## Architecture Overview

```
┌─────────────────┐     Bearer JWT      ┌──────────────────┐     Bearer JWT      ┌─────────────────┐
│  MCP Client /   │ ──────────────────► │  MCP Forex       │ ──────────────────► │  FastAPI        │
│  Strands Agent  │                     │  Server          │                     │  Currency API   │
└─────────────────┘                     └──────────────────┘                     └─────────────────┘
     (MCP_JWT_SECRET)                    (validates + forwards)                   (FAPI_JWT_SECRET)
```

## Components

| File | Description |
|------|-------------|
| `fast_api_cur_jwt_server.py` | JWT-protected FastAPI currency rate API |
| `fast_api_cur_jwt_client.py` | HTTP client to call the API with JWT |
| `mcp_forex_server_jwt.py` | MCP server: requires MCP auth, **generates** JWT for API calls |
| `mcp_forex_server_jwt_from_mcp_context.py` | MCP server: requires MCP auth, **forwards** client JWT to API |
| `mcp_forex_server_jwt_mcp_unprotexted.py` | MCP server: no MCP auth, generates JWT for API only |
| `mcp_server_bearer_token_jwt.py` | Simple MCP server with `get_private_data` tool |
| `mcp_client_bearer_jwt.py` | FastMCP client for JWT-protected MCP servers |
| `aws_strands_bearer_jwt_query.py` | AWS Strands Agent that queries MCP with JWT |
| `generate_jwt_secret.py` | Utility to generate cryptographically secure JWT secrets |

---

## Quick Start

### 1. Generate JWT Secret

```bash
cd mcp_to_api_auth
python generate_jwt_secret.py
```

Copy the output into `.env`:

```
MCP_JWT_SECRET=<generated-key>
FAPI_JWT_SECRET=<generated-key>
```

### 2. Start the API

```bash
python fast_api_cur_jwt_server.py
```

API runs at `http://localhost:8000`. Requires `rates.json` in project root.

### 3. Start the MCP Forex Server

```bash
python mcp_forex_server_jwt.py
```

MCP server runs at `http://localhost:8001/mcp`.

### 4. Query via Strands Agent

```bash
python aws_strands_bearer_jwt_query.py "What is the USD to GBP rate?"
```

---

## Configuration

### Environment Variables (.env)

| Variable | Required | Description |
|----------|----------|-------------|
| `MCP_JWT_SECRET` | Yes | Secret for MCP client/server JWT (HS256) |
| `FAPI_JWT_SECRET` | Yes | Secret for API JWT; use same as MCP for token forwarding |
| `API_BASE_URL` | No | API URL (default: `http://localhost:8000`) |
| `MCP_SERVER_URL` | No | MCP server URL (default: `http://localhost:8001/mcp`) |
| `JWT_ALGORITHM` | No | Algorithm (default: `HS256`) |

### Token Forwarding vs Generation

| Server | MCP Auth | API Token |
|--------|----------|-----------|
| `mcp_forex_server_jwt.py` | Required (MCP_JWT_SECRET) | **Generated** (FAPI_JWT_SECRET) |
| `mcp_forex_server_jwt_from_mcp_context.py` | Required (MCP_JWT_SECRET) | **Forwarded** from client |
| `mcp_forex_server_jwt_mcp_unprotexted.py` | None | Generated (FAPI_JWT_SECRET) |

For **token forwarding**, `MCP_JWT_SECRET` must equal `FAPI_JWT_SECRET` so the client's token is valid for the API.

---

## API Reference

### FastAPI Currency Rate API

**Base URL:** `http://localhost:8000`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/rate/{base}/{target}` | GET | Bearer JWT | Cross currency rate (e.g. USD→GBP) |
| `/health` | GET | None | Health check |

**Example response:**
```json
{"base": "USD", "target": "GBP", "rate": 0.78}
```

---

## MCP Tools

### mcp_forex_server_jwt / mcp_forex_server_jwt_from_mcp_context

| Tool | Args | Description |
|------|------|-------------|
| `cross_currency_rate` | `base`, `target` | Fetches rate from API (e.g. USD, GBP) |

### mcp_server_bearer_token_jwt

| Tool | Args | Description |
|------|------|-------------|
| `get_private_data` | — | Returns protected data (demo) |

---

## Usage Examples

### Call API directly (curl)

```bash
# Generate token (or use fast_api_cur_jwt_client.py logic)
TOKEN=$(python -c "
from fast_api_cur_jwt_client import create_jwt_token
print(create_jwt_token())
")

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/rate/USD/GBP
```

### Call API via Python client

```bash
python fast_api_cur_jwt_client.py USD GBP
```

### Call MCP via FastMCP client

```bash
# Start mcp_server_bearer_token_jwt first (port 8000)
python mcp_client_bearer_jwt.py
```

### Call MCP Forex via Strands Agent

```bash
# Start API (8000) and MCP Forex (8001) first
python aws_strands_bearer_jwt_query.py "Get the EUR to JPY exchange rate"
```

---

## Dependencies

```bash
pip install fastapi uvicorn fastmcp requests strands-agent-sdk python-dotenv
```

- **PyJWT** optional: `mcp_client_bearer_jwt.py` and `mcp_server_bearer_token_jwt.py` use it; others use stdlib-only JWT.

---

## File Structure

```
mcp_to_api_auth/
├── .env                    # MCP_JWT_SECRET, FAPI_JWT_SECRET
├── README.md               # This file
├── generate_jwt_secret.py  # JWT secret generator
├── fast_api_cur_jwt_server.py   # Currency API (JWT protected)
├── fast_api_cur_jwt_client.py   # API client
├── mcp_forex_server_jwt.py      # MCP→API (generates API token)
├── mcp_forex_server_jwt_from_mcp_context.py  # MCP→API (forwards token)
├── mcp_forex_server_jwt_mcp_unprotexted.py   # MCP→API (no MCP auth)
├── mcp_server_bearer_token_jwt.py           # Simple JWT MCP server
├── mcp_client_bearer_jwt.py                 # MCP client
└── aws_strands_bearer_jwt_query.py          # Strands agent
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Missing Authorization header` | Ensure `Authorization: Bearer <token>` is sent |
| `Invalid or expired token` | Regenerate token; check secret matches |
| `MCP_JWT_SECRET must be set` | Add to `.env` or run `generate_jwt_secret.py` |
| `rates.json not found` | Create `rates.json` in project root (see `../rates.json`) |
| `Connection refused` | Start API and MCP server before clients |

### rates.json Format

```json
{
  "USD": { "EUR": 0.92, "GBP": 0.78, "JPY": 150.50 },
  "EUR": { "USD": 1.09, "GBP": 0.85, "JPY": 163.20 }
}
```
