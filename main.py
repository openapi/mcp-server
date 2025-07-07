import os
import sys
import json
from typing import Dict
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from fastmcp import FastMCP
from mangum import Mangum
from memory_store import callback_results  # usa sempre il singleton globale

# Importa MCP e tool già registrati da mcp_core.py
from mcp_core import mcp

# Importa i tool (solo per triggerare la registrazione via @mcp.tool)
from apis import company, cap, trust, visurecamerali, sms

# Crea l'app ASGI MCP sulla root
mcp_app = mcp.http_app(path='/')

# Crea l'app FastAPI
app = FastAPI(lifespan=mcp_app.lifespan)



# Endpoint HTTP REST (fuori da MCP/JSON-RPC)
@app.post("/callbacks")
async def callbacks_endpoint(request: Request):
    # Ricevi il body come testo e deserializza sempre in oggetto
    raw_body = await request.body()
    print(raw_body)
    try:
        callback = json.loads(raw_body)
    except Exception:
        return {"status": "error", "message": "Body non è un JSON valido"}
    
    custom = callback.get("custom")
    if not custom:
        return {"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}
    client_id = custom.get("client_id")
    if not client_id:
        return {"status": "error", "message": "'client_id' mancante nel campo custom"}
    
    data = callback.get("data",{})
    if not data:
        return {"status": "error", "message": "'callback.data' mancante nei dati ricevuti"}
    # Determina lo stato in base a data
    state = data.get("state")
    # progress = "done" if state == "DONE" else "progress" TODO
    progress = "done"
    # Salva il risultato associato al client_id (sovrascrive se arriva una nuova callback)
    callback_results[client_id] = {
        "progress": progress,
        "result": data,
        "custom": custom
    }
    return {"status": "ok"}

@app.get("/status/{client_id}")
async def get_status(client_id: str):
    if client_id not in callback_results:
        raise HTTPException(status_code=404, detail="Risultato non trovato")
    return callback_results[client_id]

# Monta MCP sulla root, ma /callbacks viene gestito da FastAPI
app.mount("/", mcp_app)

# # Funzione entrypoint per Google Cloud Functions
# def init(request):
#     # Usa la funzione di FastAPI per gestire la richiesta WSGI di GCF
#     from fastapi import Response
#     from fastapi.responses import JSONResponse

#     # Adatta FastAPI per GCF (ASGI -> WSGI)
#     handler = Mangum(app)
#     return handler(request.environ, lambda status, headers: None)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))  # Cloud Run usa PORT, default 80
    print(f"\n--- Server FastAPI+MCP pronto su http://0.0.0.0:{port} ---", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)
