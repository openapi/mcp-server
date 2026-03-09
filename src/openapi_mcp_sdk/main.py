import os
import sys
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException, Response
from starlette.middleware.cors import CORSMiddleware
from .memory_store import get_callback_result, set_callback_result  # usa sempre il singleton globale
from .mcp_core import mcp # Import MCP instance with tools already registered in mcp_core.py
from .apis import async_tool, company, cap, trust, visurecamerali, sms, risk, geocoding,automotive,exchange, pec, docuengine, info # Import tool modules (side-effect: triggers @mcp.tool registration)

# Attempt to initialize dynamic tools if a token is present in the environment
docuengine.init_dynamic_tools()

from starlette.datastructures import MutableHeaders



# Create the MCP ASGI app mounted at root
mcp_app = mcp.http_app(path='/')

# Create the FastAPI app
app = FastAPI(lifespan=mcp_app.lifespan)

# Use asyncio.Event instead of a plain boolean flag
initialization_complete = asyncio.Event()

# Middleware: wait until initialization is complete before forwarding requests
@app.middleware("http")
async def enrich_404(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        body = json.dumps({
            "error": "not_found",
            "method": request.method,
            "path": request.url.path,
        }).encode()
        return Response(content=body, status_code=404, media_type="application/json")
    return response

@app.middleware("http")
async def wait_for_initialization(request: Request, call_next):
    await initialization_complete.wait()
    response = await call_next(request)
    return response

# Middleware: reject requests that arrive before initialization completes
@app.middleware("http")
async def check_initialization(request: Request, call_next):
    if not initialization_complete.is_set():
        raise HTTPException(status_code=503, detail="Server not initialized. Please try again later.")
    response = await call_next(request)
    return response

# Signal that server initialization is complete
def complete_initialization():
    initialization_complete.set()

# Call once server initialization is done
complete_initialization()

# Lock to prevent concurrent duplicate registrations
registration_lock = asyncio.Lock()

# Middleware: lift token from query string into the Authorization header
@app.middleware("http")
async def token_querystring_to_authorization(request: Request, call_next):
    token = request.query_params.get("token")
    if token:
        # Strip any existing Authorization headers
        headers = [
            (k, v)
            for k, v in request.scope["headers"]
            if k.lower() != b"authorization"
        ]
        # Inject the Authorization header
        headers.append((b"authorization", f"Bearer {token}".encode()))
        request.scope["headers"] = headers
    else:
        # Not in query string — try reading from the Authorization header for JIT registration
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth[7:]

    # JIT Registration: if we have a token and tools are not yet registered, proceed
    if token and not getattr(app.state, "dynamic_tools_registered", False):
        async with registration_lock:
            if not getattr(app.state, "dynamic_tools_registered", False):
                print(f"JIT Registration: initializing dynamic tools with detected token (starts with: {token[:8]}...)")
                success = docuengine.init_dynamic_tools(token)
                if success:
                    app.state.dynamic_tools_registered = True
                else:
                    print("JIT Registration failed. Will retry on next request if token is provided.")

    response = await call_next(request)
    return response

# Middleware: intercept OAuth discovery requests before routing.
# The catch-all Starlette mount at "/" would otherwise return plain "Not Found"
# which MCP clients fail to parse as JSON. We return a proper JSON 404 so
# clients understand OAuth is not supported and fall back to Bearer token auth.
_OAUTH_NOT_SUPPORTED_BODY = json.dumps({
    "error": "oauth_not_supported",
    "message": "This server does not support OAuth. Use a pre-configured Bearer token in the Authorization header."
}).encode()

_OAUTH_DISCOVERY_PATHS = {
    "/.well-known/oauth-authorization-server",
    "/.well-known/oauth-protected-resource",
    "/.well-known/openid-configuration",
}

@app.middleware("http")
async def reject_oauth_discovery(request: Request, call_next):
    if request.url.path.rstrip("/") in {p.rstrip("/") for p in _OAUTH_DISCOVERY_PATHS}:
        return Response(
            content=_OAUTH_NOT_SUPPORTED_BODY,
            status_code=404,
            media_type="application/json",
        )
    return await call_next(request)

# Plain HTTP REST endpoints (outside MCP/JSON-RPC)
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

# CORS — must be added LAST (after all @app.middleware decorators) so it becomes
# the outermost middleware.  Starlette uses insert(0)+reversed() to build the
# stack, meaning the last-added middleware executes first on every request.
# expose_headers is required for the browser to read the Mcp-Session-Id header.
# allow_credentials must NOT be True when allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"],
)

# Mount MCP at root; /callbacks and /status/* are handled by FastAPI above
app.mount("/", mcp_app)


def run():
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
