import os
import sys
import json
from fastapi import FastAPI, Request, HTTPException, Response
from .memory_store import get_callback_result, set_callback_result  # usa sempre il singleton globale
from .mcp_core import mcp # Importa MCP e tool già registrati da mcp_core.py
from .apis import async_tool, company, cap, trust, visurecamerali, sms, risk, geocoding,automotive,exchange, pec, docuengine, info # Importa i tool (solo per triggerare la registrazione via @mcp.tool)

# Tenta l'inizializzazione dei tool dinamici (se è presente un token in ambiente)
docuengine.init_dynamic_tools()

import asyncio
# TODO: Remove legacy dependency — google-cloud-storage is used only to serve downloaded files
# from a GCS bucket named after K_SERVICE. Replace the /status/{id}/files/{name} endpoint with
# a storage-agnostic solution: local filesystem for dev (e.g. /tmp), pluggable via a
# STORAGE_BACKEND env var (local | s3 | gcs). Remove google-cloud-storage from requirements.txt
# and pyproject.toml when done.
from google.cloud import storage
from starlette.datastructures import MutableHeaders



# Crea l'app ASGI MCP sulla root
mcp_app = mcp.http_app(path='/')

# Crea l'app FastAPI
app = FastAPI(lifespan=mcp_app.lifespan)

# Sostituzione del flag globale con asyncio.Event
initialization_complete = asyncio.Event()

# Middleware per attendere il completamento dell'inizializzazione
@app.middleware("http")
async def wait_for_initialization(request: Request, call_next):
    await initialization_complete.wait()
    response = await call_next(request)
    return response

# Middleware per bloccare le richieste prima dell'inizializzazione
@app.middleware("http")
async def check_initialization(request: Request, call_next):
    if not initialization_complete.is_set():
        raise HTTPException(status_code=503, detail="Server not initialized. Please try again later.")
    response = await call_next(request)
    return response

# Funzione per completare l'inizializzazione del server
def complete_initialization():
    initialization_complete.set()

# Chiamare questa funzione al termine dell'inizializzazione del server
complete_initialization()

# Lock per evitare registrazioni multiple simultanee
registration_lock = asyncio.Lock()

# Middleware per intercettare il token nella querystring e inserirlo nell'header Authorization
@app.middleware("http")
async def token_querystring_to_authorization(request: Request, call_next):
    token = request.query_params.get("token")
    if token:
        # Rimuovi eventuali header Authorization già presenti
        headers = [
            (k, v)
            for k, v in request.scope["headers"]
            if k.lower() != b"authorization"
        ]
        # Aggiungi il nuovo header Authorization
        headers.append((b"authorization", f"Bearer {token}".encode()))
        request.scope["headers"] = headers
    else:
        # Se non c'è in querystring, prova a prenderlo dagli header per la registrazione JIT
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth[7:]

    # JIT Registration: Se abbiamo un token e i tool non sono registrati, procedi
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

# Endpoint HTTP REST (fuori da MCP/JSON-RPC)
@app.post("/callbacks")
async def callbacks_endpoint(request: Request):
    # Ricevi il body come testo e deserializza sempre in oggetto
    raw_body = await request.body()
    try:
        callback = json.loads(raw_body)
    except Exception:
        print("Body not a valid JSON")
        return {"status": "error", "message": "Body not a valid JSON"}
    
    cb_obj = callback.get("callback")
    custom = callback.get("custom") or (cb_obj.get("data") if isinstance(cb_obj, dict) else None)
    if not custom:
        print("'callback.custom' mancante nei dati ricevuti")
        return {"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}
    request_id = custom.get("request_id")
    if not request_id:
        print("'request_id' mancante nel campo custom")
        return {"status": "error", "message": "'request_id' mancante nel campo custom"}
    
    data = callback.get("data",{}) or callback
    if not data:
        print("'callback.data' mancante nei dati ricevuti")
        return {"status": "error", "message": "'callback.data' mancante nei dati ricevuti"}
    
    # Salva il risultato associato al client_id (sovrascrive se arriva una nuova callback)
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

# Monta MCP sulla root, ma /callbacks viene gestito da FastAPI
app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn
    # TODO: Remove legacy dependency — PORT env var defaulting to 80 follows Google Cloud Run
    # convention. Standard default should be 8080 (or configurable). Update Dockerfile EXPOSE
    # and Makefile accordingly when decoupled.
    port = int(os.environ.get("PORT", 80))  # Cloud Run usa PORT, default 80
    print(f"\n--- Server FastAPI+MCP ready on http://0.0.0.0:{port} ---", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)
