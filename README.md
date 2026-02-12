# MCP and Agents

Model Context Protocol (MCP) servers, HTTP proxy, and AI agents that consume MCP tools. Built with [FastMCP](https://gofastmcp.com/), with optional integration for Strands and Google ADK agents.

## Overview

- **MCP servers** expose tools over HTTP (forex rates, weather, LLM sampling).
- **MCP proxy** aggregates one or more backend MCP servers behind a single endpoint.
- **Clients and agents** (FastMCP client, Strands, Google ADK) call tools via direct or proxied MCP.

## Project structure

| Path | Description |
|------|-------------|
| `mcp_forex_server.py` | Forex MCP server (port 8001). Tool: `cross_currency_rate(base, target)`. |
| `mcp_weather_server.py` | Weather MCP server. Tool: `get_current_weather(city_name)` (Google Maps + NWS API). |
| `mcp_server_sampling_llm.py` | MCP server with LLM sampling (e.g. `generate_smart_filename`, `summarize`, `collect_user_info`). |
| `mcp_proxy.py` | Single-backend proxy → forex server; runs on port 8003. |
| `mcp_proxy_config.py` | Multi-backend proxy (forex, weather, optional remote); runs on port 8003. |
| `mcp_client.py` | FastMCP client: lists tools and calls a tool (e.g. forex) via direct or proxy URL. |
| `aws_strands_agent.py` | Strands agent using MCP tools over streamable HTTP. |
| `tool_agent/agent.py` | Google ADK agent (Gemini) with `MCPToolset`; can use proxy or individual servers. |
| `fast_api_cur.py` | FastAPI app serving forex rates from `rates.json` at `/rate/{base}/{target}` (used by forex MCP). |
| `rates.json` | Currency rates data for the forex API. |

Utilities and related scripts: `city_coords_google_map.py`, `nws_api_call_googlemaps.py`, `aws_strands_agent_cmd_input.py`, `aws_strands_agent_cmd_hook.py`.

## Setup

1. **Environment**
   - Copy `.env.example` to `.env` if present; otherwise create `.env` with any required keys.
   - For weather: set `GOOGLE_MAPS_API_KEY`.
   - For LLM sampling: set `OPENAI_API_KEY` (or equivalent) as needed by `mcp_server_sampling_llm.py`.
   - `tool_agent/` may have its own `.env` for the ADK agent (e.g. Gemini).

2. **Dependencies**
   - Install FastMCP, requests, python-dotenv, and (as needed) googlemaps, openai, Strands, Google ADK, FastAPI/uvicorn.
   - Example (adjust to your environment):
   ```bash
   pip install fastmcp requests python-dotenv googlemaps openai fastapi uvicorn
   ```

## Running

**Forex backend (required for forex MCP):**
```bash
uvicorn fast_api_cur:app --host 0.0.0.0 --port 8000
```

**MCP servers:**
```bash
# Forex MCP (port 8001)
python mcp_forex_server.py

# Weather MCP (default port, e.g. 8002)
python mcp_weather_server.py

# LLM sampling MCP (if used)
python mcp_server_sampling_llm.py
```

**MCP proxy (use one):**
```bash
# Single backend (forex only)
python mcp_proxy.py

# Multiple backends (forex, weather, etc.)
python mcp_proxy_config.py
```

**Client / agents:**
```bash
# List tools and call a tool (edit mcp_client.py to use mcp_url or proxy_url)
python mcp_client.py

# Strands agent (ensure forex MCP or proxy is running)
python aws_strands_agent.py

# Google ADK tool agent (configure URLs in tool_agent/agent.py)
# Run via your ADK entrypoint (e.g. agent.py)
```

In `mcp_client.py`, set `mcp_url` for direct MCP or `proxy_url` for the proxy. In `tool_agent/agent.py`, point `MCPToolset` at the desired server URL (e.g. `proxy_mcp_server_url`).

## Ports (defaults)

| Service | Port |
|--------|------|
| Forex rates API (`fast_api_cur`) | 8000 |
| Forex MCP server | 8001 |
| Weather MCP server | 8002 |
| MCP proxy | 8003 |

## License

See repository or project root for license information.
