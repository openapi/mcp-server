import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send, Message
from .mcp_audit import McpAuditMiddleware
from .memory_store import get_callback_result, set_callback_result
from .mcp_core import mcp # Import MCP instance with tools already registered in mcp_core.py
from .apis import async_tool, company, cap, trust, visurecamerali, sms, risk, geocoding,automotive,exchange, pec, docuengine, info # Import tool modules (side-effect: triggers @mcp.tool registration)

# Create the MCP ASGI app mounted at root
mcp_app = mcp.http_app(path='/')

# Create the FastAPI app
app = FastAPI(lifespan=mcp_app.lifespan)

# Attempt to initialize dynamic tools if a token is present in the environment.
# Mark as registered on app.state so JIT registration is skipped for this session.
if docuengine.init_dynamic_tools():
    app.state.dynamic_tools_registered = True

# Lock to prevent concurrent duplicate registrations
registration_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Pure ASGI middlewares — avoid BaseHTTPMiddleware so that SSE / streaming
# responses from FastMCP pass through untouched.  BaseHTTPMiddleware buffers
# the response in an anyio channel and cannot properly forward streaming
# bodies, causing "RuntimeError: No response returned." on POST / requests.
# ---------------------------------------------------------------------------

class Enrich404Middleware:
    """Replace plain 404 responses with a structured JSON body."""
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_404 = False

        async def send_wrapper(message: Message) -> None:
            nonlocal is_404
            if message["type"] == "http.response.start":
                if message.get("status") == 404:
                    is_404 = True
                    body = json.dumps({
                        "error": "not_found",
                        "method": scope["method"],
                        "path": scope["path"],
                    }).encode()
                    await send({
                        "type": "http.response.start",
                        "status": 404,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    })
                    await send({"type": "http.response.body", "body": body, "more_body": False})
                else:
                    await send(message)
            elif not is_404:
                # Pass through body messages only for non-404 responses
                await send(message)

        await self.app(scope, receive, send_wrapper)


class TokenQuerystringMiddleware:
    """Lift ?token=<value> from the query string into an Authorization: Bearer header.
    Also triggers JIT registration of dynamic tools on first authenticated request.
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from urllib.parse import parse_qs, urlencode
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string, keep_blank_values=True)
        token: str | None = (params.pop("token", None) or [None])[0]

        if token:
            # Strip any existing Authorization header and inject the new one.
            # Also remove ?token= from the query string so it never appears in
            # access logs — the token travels as a header from this point on.
            clean_qs = urlencode(params, doseq=True).encode()
            headers = [(k, v) for k, v in scope["headers"] if k.lower() != b"authorization"]
            headers.append((b"authorization", f"Bearer {token}".encode()))
            scope = {**scope, "headers": headers, "query_string": clean_qs}
        else:
            # Not in query string — try reading from the Authorization header for JIT registration
            for k, v in scope["headers"]:
                if k.lower() == b"authorization":
                    val = v.decode()
                    if val.lower().startswith("bearer "):
                        token = val[7:]
                    break

        # JIT Registration: if we have a token and tools are not yet registered, proceed.
        # Run the sync HTTP call in a thread so we never block the event loop.
        if token and not getattr(app.state, "dynamic_tools_registered", False):
            async with registration_lock:
                if not getattr(app.state, "dynamic_tools_registered", False):
                    print(f"JIT Registration: initializing dynamic tools with detected token (starts with: {token[:8]}...)")
                    success = await asyncio.to_thread(docuengine.init_dynamic_tools, token)
                    if success:
                        app.state.dynamic_tools_registered = True
                    else:
                        print("JIT Registration failed. Will retry on next request if token is provided.")

        await self.app(scope, receive, send)


_OAUTH_NOT_SUPPORTED_BODY = json.dumps({
    "error": "oauth_not_supported",
    "message": "This server does not support OAuth. Use a pre-configured Bearer token in the Authorization header."
}).encode()

_OAUTH_DISCOVERY_PATHS = {
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/openid-configuration",
}

class RejectOAuthDiscoveryMiddleware:
    """Return a JSON 404 for OAuth discovery endpoints so MCP clients fall back to Bearer auth."""
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].rstrip("/") in {p.rstrip("/") for p in _OAUTH_DISCOVERY_PATHS}:
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({"type": "http.response.body", "body": _OAUTH_NOT_SUPPORTED_BODY, "more_body": False})
            return
        await self.app(scope, receive, send)


# Register middlewares.
# add_middleware inserts at position 0 each time, so the LAST call here becomes
# the outermost wrapper (executed first on every request).
# Desired execution order (outer → inner):
#   CORS → RejectOAuth → TokenQuerystring → Enrich404 → McpAudit → FastAPI router
app.add_middleware(McpAuditMiddleware)            # innermost — logs MCP JSON-RPC actions
app.add_middleware(Enrich404Middleware)           # wraps 404s in JSON
app.add_middleware(TokenQuerystringMiddleware)    # injects auth header + JIT registration
app.add_middleware(RejectOAuthDiscoveryMiddleware) # short-circuits OAuth discovery paths
# CORS must be outermost so it runs before anything else on every request,
# including pre-flight OPTIONS. expose_headers exposes Mcp-Session-Id to browsers.
# allow_credentials must NOT be True when allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)


# ---------------------------------------------------------------------------
# Plain HTTP REST endpoints (outside MCP/JSON-RPC)
# ---------------------------------------------------------------------------

@app.post("/callbacks")
async def callbacks_endpoint(request: Request):
    # Read raw body and deserialize to an object
    raw_body = await request.body()
    try:
        callback = json.loads(raw_body)
    except Exception:
        print("Body not a valid JSON")
        return {"status": "error", "message": "Body not a valid JSON"}

    cb_obj = callback.get("callback")
    custom = callback.get("custom") or (cb_obj.get("data") if isinstance(cb_obj, dict) else None)
    if not custom:
        print("'callback.custom' missing from received data")
        return {"status": "error", "message": "'callback.custom' missing from received data"}
    request_id = custom.get("request_id")
    if not request_id:
        print("'request_id' missing from custom field")
        return {"status": "error", "message": "'request_id' missing from custom field"}

    data = callback.get("data",{}) or callback
    if not data:
        print("'callback.data' missing from received data")
        return {"status": "error", "message": "'callback.data' missing from received data"}

    # Store the result keyed by request_id (overwrites on subsequent callbacks)
    set_callback_result(request_id, data, custom)

    print(f"Callback: \n{data}\n")

    return {"status": "ok"}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    try:
        return get_callback_result(request_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Not Found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/status/{request_id}/files/{file_name}")
async def get_file(request_id: str,file_name: str):
    try:
        # TODO: Remove legacy dependency — GCS bucket name is taken from K_SERVICE (Cloud Run env var).
        # Replace with a storage-agnostic file retrieval: read from local disk (STORAGE_PATH env var)
        # for dev, or from a configurable bucket/prefix via STORAGE_BACKEND / STORAGE_BUCKET env vars.
        from google.cloud import storage  # lazy import — optional legacy dependency
        storage_client = storage.Client()
        bucket = storage_client.bucket(os.getenv("K_SERVICE"))
        blob = bucket.blob(f"{request_id}/{file_name}")

        if not blob.exists():
            raise HTTPException(status_code=404, detail="File not found")

        file_content = blob.download_as_bytes()
        content_type = blob.content_type or "application/octet-stream"
        return Response(content=file_content, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

# Mount MCP at root; /callbacks and /status/* are handled by FastAPI above
app.mount("/", mcp_app)


def run():
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
