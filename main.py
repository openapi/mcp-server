import os
import sys
import json
from typing import Dict
from fastapi import FastAPI, Request, HTTPException
from memory_store import get_callback_result, set_callback_result  # usa sempre il singleton globale
from mcp_core import mcp # Importa MCP e tool già registrati da mcp_core.py
from apis import async_tool, company, cap, trust, visurecamerali, sms, risk, geocoding,automotive,exchange # Importa i tool (solo per triggerare la registrazione via @mcp.tool)



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
        print("Body not a valid JSON")
        return {"status": "error", "message": "Body not a valid JSON"}
    
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
    set_callback_result(request_id, data, custom)

    return {"status": "ok"}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    try:
        return get_callback_result(request_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Not Found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Monta MCP sulla root, ma /callbacks viene gestito da FastAPI
app.mount("/", mcp_app)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))  # Cloud Run usa PORT, default 80
    print(f"\n--- Server FastAPI+MCP pronto su http://0.0.0.0:{port} ---", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)
