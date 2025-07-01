import os
import sys
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastmcp import FastMCP
from mangum import Mangum

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
    data = await request.json()
    callback_custom = data.get("callback", {}).get("custom") if isinstance(data.get("callback"), dict) else None
    if not callback_custom:
        return {"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}
    # Qui puoi chiamare mcp.notify o altra logica
    # mcp.notify(callback_custom, {
    #     "type": "callback",
    #     "payload": data
    # })
    return {"status": "ok"}

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
    print(f"\n--- Server FastAPI+MCP pronto su http://0.0.0.0:80 ---", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=80)
