import os
import sys
import requests
from fastmcp import FastMCP, Context
from fastapi import Request
from typing import Dict, Any, Optional
from pydantic import BaseModel
from mcp_core import mcp, make_api_call

# --- Modello Pydantic per Risposte di Errore Standard ---
class ApiError(BaseModel):
    error: str
    message: str

# --- Importa i tool ---
from apis import company, cap, trust, visurecamerali, sms

# Endpoint FastAPI per ricevere callback asincrone
if hasattr(mcp, 'app'):
    from fastapi import APIRouter
    router = APIRouter()

    @router.post("/callbacks/")
    async def callbacks_endpoint(request: Request):
        data = await request.json()
        # Verifica che 'callback' e 'custom' siano presenti nei dati
        callback_custom = data.get("callback", {}).get("custom") if isinstance(data.get("callback"), dict) else None
        if not callback_custom:
            return {"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}
        # Inoltra la callback come Notification MCP a tutti i client
        mcp.notify(callback_custom, {
            "type": "callback",
            "payload": data
        })
        return {"status": "ok"}

    mcp.app.include_router(router)

def init(request):
    return mcp.app(request)

if __name__ == "__main__":
    try:
        print(f"\n--- Server Pronto ---", file=sys.stderr)
        print("Per avviare in modalità remota, eseguire:", file=sys.stderr)
        print("python server.py", file=sys.stderr)
        mcp.run(transport="http", host="0.0.0.0", port=8080)
    except Exception as e:
        print(f"ERRORE AVVIO SERVER: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
