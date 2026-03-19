# MCP to SQL with JWT

MCP server that queries SQLite `sales.db` with JWT authentication. The tool `get_my_clients` returns clients for the salesperson identified by `context.username` in the JWT.

## Files

| File | Description |
|------|-------------|
| `mcp_server_sqlite_jwt.py` | MCP server with JWT auth; tool queries sales.db |
| `mcp_client_sqlite_jwt.py` | Client with JWT (context.username) |
| `init_sqlite_db.py` | Creates sales.db and sample data |
| `generate_jwt_with_username.py` | Generate JWT for testing |
| `.env` | MCP_JWT_SECRET |

## Quick Start

```bash
cd mcp_to_sql_jwt

# 1. Initialize DB (if needed)
python init_sqlite_db.py

# 2. Start server (port 8011)
python mcp_server_sqlite_jwt.py

# 3. In another terminal, run client
python mcp_client_sqlite_jwt.py

# As another salesperson
SALES_USER="Bob Martinez" python mcp_client_sqlite_jwt.py
```

## JWT Format

Payload must include:

```json
{"context": {"username": "Alice Chen"}, "iat": 1234567890, "exp": 1234571490}
```

The tool uses `context.username` to query `sales_clients` in sales.db.

## Auth

- **Authorization header**: `Bearer <JWT>`
- **auth_token argument**: For transports that don't forward headers (e.g. streamable HTTP), pass JWT as `auth_token` tool argument.

## Dependencies

```bash
pip install fastmcp mcp python-dotenv
```
