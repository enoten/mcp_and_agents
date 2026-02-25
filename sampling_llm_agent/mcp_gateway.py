import os
import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import httpx
import websockets
from websockets import ConnectionClosedOK, ConnectionClosedError

# Optional fastmcp integration
try:
    import fastmcp  # type: ignore
    HAS_FASTMCP = True
except Exception:
    fastmcp = None
    HAS_FASTMCP = False

LOG = logging.getLogger("mcp_gateway")
logging.basicConfig(level=logging.INFO)

# Config
PROXY_URL = os.environ.get("FASTMCP_PROXY_URL", "http://localhost:8001")
PROXY_WS_URL = os.environ.get("FASTMCP_PROXY_WS_URL", "ws://localhost:8001/ws")
LISTEN_HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("FASTMCP_PORT", "8080"))
HTTP_TIMEOUT = float(os.environ.get("FASTMCP_HTTP_TIMEOUT", "15"))

app = FastAPI(title="MCP Gateway")

def encode_message(payload: Any) -> bytes:
    if HAS_FASTMCP and hasattr(fastmcp, "serialize"):
        return fastmcp.serialize(payload)
    # default: send JSON bytes
    return json.dumps(payload).encode("utf-8")

def decode_message(data: bytes) -> Any:
    if HAS_FASTMCP and hasattr(fastmcp, "deserialize"):
        return fastmcp.deserialize(data)
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return data.decode("utf-8")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "proxy": PROXY_URL})

@app.post("/send")
async def send(request: Request):
    """
    Forward a JSON payload to the configured FastMCP proxy HTTP endpoint.
    Expected body: JSON object with fields such as {"channel": "agentX", "payload": {...}}
    Returns proxy response (JSON).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")

    # Try to forward to a few common proxy endpoints
    target_paths = ["/mcp", "/api/mcp", "/proxy/mcp", "/v1/mcp"]
    headers = {"content-type": "application/octet-stream" if HAS_FASTMCP else "application/json"}
    data = encode_message(payload)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        last_exc = None
        for p in target_paths:
            url = PROXY_URL.rstrip("/") + p
            try:
                LOG.info("Forwarding to proxy HTTP %s", url)
                resp = await client.post(url, content=data, headers=headers)
                content_type = resp.headers.get("content-type", "")
                resp_bytes = resp.content
                # Decode if JSON or fastmcp
                try:
                    if "application/json" in content_type:
                        return JSONResponse(resp.json(), status_code=resp.status_code)
                except Exception:
                    pass
                # fallback: decode bytes
                try:
                    decoded = decode_message(resp_bytes)
                    return JSONResponse({"status_code": resp.status_code, "response": decoded})
                except Exception:
                    return JSONResponse({"status_code": resp.status_code, "raw": resp_bytes.hex()})
            except Exception as e:
                last_exc = e
                LOG.debug("proxy HTTP forward failed for %s: %s", url, e)

        raise HTTPException(status_code=502, detail=f"failed to forward to proxy: {last_exc}")

@app.websocket("/ws")
async def websocket_proxy(ws: WebSocket):
    """
    Open a WebSocket to the gateway and proxy frames to the configured FastMCP websocket.
    Messages are forwarded bidirectionally. Messages from HTTP clients are expected to be JSON (or fastmcp bytes encoded as base64 if you prefer).
    """
    await ws.accept()
    proxy_ws_url = PROXY_WS_URL

    # Connect to backend proxy websocket
    try:
        LOG.info("Connecting to proxy websocket %s", proxy_ws_url)
        async with websockets.connect(proxy_ws_url) as proxy_ws:
            async def client_to_proxy():
                try:
                    while True:
                        msg = await ws.receive_text()
                        # try to parse JSON; if not JSON, send as raw
                        try:
                            obj = json.loads(msg)
                            outbound = encode_message(obj)
                            await proxy_ws.send(outbound)
                        except json.JSONDecodeError:
                            # treat incoming as plain text
                            await proxy_ws.send(msg)
                except WebSocketDisconnect:
                    LOG.info("Client WebSocket disconnected")
                    try:
                        await proxy_ws.close()
                    except Exception:
                        pass
                except Exception as e:
                    LOG.exception("client->proxy error: %s", e)
                    try:
                        await proxy_ws.close()
                    except Exception:
                        pass

            async def proxy_to_client():
                try:
                    async for raw in proxy_ws:
                        # raw may be bytes or str depending on remote library
                        if isinstance(raw, (bytes, bytearray)):
                            try:
                                decoded = decode_message(bytes(raw))
                                await ws.send_text(json.dumps({"type":"mcp","payload":decoded}))
                            except Exception:
                                # fallback: send base64 or hex
                                await ws.send_text(bytes(raw).hex())
                        else:
                            # text frame
                            await ws.send_text(raw)
                except (ConnectionClosedOK, ConnectionClosedError):
                    LOG.info("Proxy websocket closed")
                    try:
                        await ws.close()
                    except Exception:
                        pass
                except Exception as e:
                    LOG.exception("proxy->client error: %s", e)
                    try:
                        await ws.close()
                    except Exception:
                        pass

            # run both tasks concurrently until one finishes
            await asyncio.gather(client_to_proxy(), proxy_to_client())
    except Exception as e:
        LOG.exception("Failed to connect to proxy websocket: %s", e)
        try:
            await ws.close(code=1011)
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sampling_llm_agent.mcp_gateway:app", host=LISTEN_HOST, port=LISTEN_PORT, reload=False)