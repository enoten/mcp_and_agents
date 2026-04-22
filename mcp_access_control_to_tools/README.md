# MCP Access Control

This README documents the `mcp_ac` example that uses only:

- `mcp_ac/mcp_server.py`
- `mcp_ac/mcp_client.py`

## Purpose

The example demonstrates MCP tool-level authorization with JWT identity:

- client builds JWT tokens manually (no jwt library),
- server validates JWT signature and expiry manually,
- identity is extracted from JWT payload (`identity` or `sub`),
- tool visibility and tool execution are restricted by identity.

## Files

- `mcp_ac/mcp_server.py`
  - FastMCP server with middleware-based access control
  - Implements manual JWT decode and HS256 signature verification
  - Defines two tools: `current_time`, `current_weather`
  - Enforces:
    - `identity_1` -> only `current_time`
    - `identity_2` -> both tools

- `mcp_ac/mcp_client.py`
  - FastMCP client using `StreamableHttpTransport`
  - Implements manual JWT creation and HS256 signing
  - Sends JWT as `Authorization: Bearer <token>`
  - Runs three scenarios (two allowed listings + one forbidden tool call)

## Environment Variables

Create `mcp_ac/.env` with:

```env
MCP_URL=http://localhost:8011/mcp
MCP_JWT_SECRET=replace_with_a_strong_secret
MCP_JWT_ALGORITHM=HS256
```

Notes:

- Both client and server must use the same `MCP_JWT_SECRET`.
- This sample supports only `HS256`.

## Run

From repository root:

```bash
python mcp_ac/mcp_server.py
```

In another terminal:

```bash
python mcp_ac/mcp_client.py
```

## Expected Results

- Scenario A (`identity_1`) -> `tools/list` returns `['current_time']`
- Scenario B (`identity_2`) -> `tools/list` returns `['current_time', 'current_weather']`
- Scenario C (`identity_1` calling `current_weather`) -> access denied
