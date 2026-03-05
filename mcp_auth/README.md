# MCP Auth

MCP (Model Context Protocol) servers and clients with Bearer token and JWT authentication. Demonstrates two auth patterns: simple static Bearer tokens and JWT-based auth.

## Components

| File | Type | Auth | Description |
|------|------|------|-------------|
| `mcp_server_bearer_token_jwt.py` | Server | JWT (PyJWT) | MCP server with `get_private_data` tool |
| `mcp_server_bearer_token.py` | Server | Static Bearer token | Same tool, simpler auth |
| `mcp_client_bearer_jwt.py` | Client | JWT (PyJWT) | FastMCP client for JWT server |
| `mcp_client_bearer.py` | Client | Static Bearer token | FastMCP client for token server |
| `aws_strands_bearer_jwt.py` | Client | JWT (stdlib) | AWS Strands Agent for JWT server |

---

## Auth Patterns

### 1. Static Bearer Token

- **Server:** `mcp_server_bearer_token.py` – expects `Authorization: Bearer <MCP_BEARER_TOKEN>`
- **Client:** `mcp_client_bearer.py` – sends fixed token from env
- **Use case:** Simple dev/testing, single shared secret

### 2. JWT (HS256)

- **Server:** `mcp_server_bearer_token_jwt.py` – validates JWT with `MCP_JWT_SECRET`
- **Clients:** `mcp_client_bearer_jwt.py` (PyJWT), `aws_strands_bearer_jwt.py` (stdlib)
- **Use case:** Expiring tokens, standard auth, production-ready

---

## Quick Start

### JWT Flow

**1. Configure `.env`:**

```
MCP_JWT_SECRET=your-256-bit-secret-key
```

**2. Start the JWT server:**

```bash
cd mcp_auth
python mcp_server_bearer_token_jwt.py
```

Server runs at `http://localhost:8000/mcp`.

**3. Call with FastMCP client:**

```bash
python mcp_client_bearer_jwt.py
```

**4. Or call with Strands Agent:**

```bash
python aws_strands_bearer_jwt.py
```

### Static Token Flow

**1. Configure `.env` (optional):**

```
MCP_BEARER_TOKEN=my-secret-token
```

**2. Start the token server:**

```bash
python mcp_server_bearer_token.py
```

**3. Call with client:**

```bash
python mcp_client_bearer.py
```

---

## Configuration

### Environment Variables

| Variable | Server | Client | Description |
|----------|--------|--------|-------------|
| `MCP_JWT_SECRET` | JWT server | JWT clients | Secret for JWT signing/verification |
| `MCP_JWT_ALGORITHM` | JWT server | JWT clients | Algorithm (default: HS256) |
| `MCP_BEARER_TOKEN` | Token server | Token client | Static shared token |
| `MCP_SERVER_URL` | — | Clients | MCP endpoint (default: `http://localhost:8000/mcp`) |
| `MCP_SERVER_HOST` | Servers | — | Bind host (default: 0.0.0.0) |
| `MCP_SERVER_PORT` | Servers | — | Port (default: 8000) |

---

## MCP Tools

Both servers expose:

| Tool | Args | Description |
|------|------|-------------|
| `get_private_data` | — | Returns protected data (demo) |

---

## File Details

### mcp_server_bearer_token_jwt.py

- Uses **PyJWT** to verify tokens
- Middleware checks `Authorization: Bearer <jwt>` on every tool call
- Rejects invalid or expired tokens with `ToolError`

### mcp_server_bearer_token.py

- Compares `Authorization: Bearer <token>` to `MCP_BEARER_TOKEN`
- No JWT; fixed string match
- Minimal dependencies (no PyJWT)

### mcp_client_bearer_jwt.py

- Uses **PyJWT** to create tokens
- FastMCP `Client` with `BearerAuth(token)`
- Calls `get_private_data` and prints result

### mcp_client_bearer.py

- Sends `MCP_BEARER_TOKEN` as Bearer auth
- No JWT; uses env var directly

### aws_strands_bearer_jwt.py

- Uses **stdlib-only** JWT creation (no PyJWT)
- Connects via `streamablehttp_client` with `Authorization` header
- Strands `Agent` with MCP tools; natural language queries

---

## Dependencies

```bash
pip install -r requirements.txt
# fastmcp, PyJWT
```

For `aws_strands_bearer_jwt.py` only:

```bash
pip install strands-agent-sdk mcp
```

**Note:** `mcp_client_bearer_jwt.py` and `mcp_server_bearer_token_jwt.py` require PyJWT. `aws_strands_bearer_jwt.py` uses stdlib JWT (no PyJWT).

---

## Usage Examples

### FastMCP Client (JWT)

```bash
cd mcp_auth
python mcp_client_bearer_jwt.py
```

Output: `This is protected data.`

### Strands Agent (JWT)

```bash
python aws_strands_bearer_jwt.py
```

Agent uses natural language to call `get_private_data`.

### Static Token

```bash
# Terminal 1
python mcp_server_bearer_token.py

# Terminal 2
python mcp_client_bearer.py
```

---

## File Structure

```
mcp_auth/
├── .env                    # MCP_JWT_SECRET, MCP_BEARER_TOKEN
├── README.md               # This file
├── requirements.txt        # fastmcp, PyJWT
├── mcp_server_bearer_token_jwt.py   # JWT server
├── mcp_server_bearer_token.py       # Static token server
├── mcp_client_bearer_jwt.py         # JWT client (FastMCP)
├── mcp_client_bearer.py             # Token client (FastMCP)
└── aws_strands_bearer_jwt.py       # JWT client (Strands Agent)
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Missing or invalid Authorization header` | Ensure client sends `Authorization: Bearer <token>` |
| `Invalid or expired token` | Regenerate JWT; verify `MCP_JWT_SECRET` matches server |
| `MCP_JWT_SECRET must be set` | Add to `.env` |
| `ModuleNotFoundError: No module named 'jwt'` | Run `pip install PyJWT` (for JWT server/client) |
| `MCPClientInitializationError` | Start MCP server first; check `MCP_SERVER_URL` and port |

### Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add output to `.env` as `MCP_JWT_SECRET=...`.
