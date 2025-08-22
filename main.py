import os
import sys
import json
from typing import Dict
from fastapi import FastAPI, Request, HTTPException
from memory_store import callback_results  # usa sempre il singleton globale
from mcp_core import mcp # Importa MCP e tool già registrati da mcp_core.py
from apis import company, cap, trust, visurecamerali, sms, risk, geocoding,automotive,exchange # Importa i tool (solo per triggerare la registrazione via @mcp.tool)



# Crea l'app ASGI MCP sulla root
mcp_app = mcp.http_app(path='/')

# Crea l'app FastAPI
app = FastAPI(lifespan=mcp_app.lifespan)

# Endpoint HTTP REST (fuori da MCP/JSON-RPC)
@app.post("/callbacks")
async def callbacks_endpoint(request: Request):
    # Ricevi il body come testo e deserializza sempre in oggetto
    raw_body = await request.body()
    try:
        callback = json.loads(raw_body)
    except Exception:
        print("Body non è un JSON valido")
        return {"status": "error", "message": "Body non è un JSON valido"}
    
    custom = callback.get("custom") or callback.get("callback").get("data")
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
    callback_results[request_id] = {
        "data": data,
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))  # Cloud Run usa PORT, default 80
    print(f"\n--- Server FastAPI+MCP pronto su http://0.0.0.0:{port} ---", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)
