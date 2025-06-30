import os
import sys
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

# --- FASTAPI CALLBACK ENDPOINT (solo se MCP server) ---
if hasattr(mcp, 'app'):
    from fastapi import APIRouter
    router = APIRouter()

    @router.post("/callbacks/")
    async def callbacks_endpoint(request: Request):
        data = await request.json()
        callback_custom = data.get("callback", {}).get("custom") if isinstance(data.get("callback"), dict) else None
        if not callback_custom:
            return {"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}
        mcp.notify(callback_custom, {
            "type": "callback",
            "payload": data
        })
        return {"status": "ok"}

    mcp.app.include_router(router)

# --- FLASK CALLBACK ENDPOINT (solo per Cloud Functions) ---
try:
    from flask import Flask, request as flask_request, jsonify
    app = Flask(__name__)

    @app.route("/callbacks/", methods=["POST"])
    def flask_callbacks_endpoint():
        data = flask_request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Dati JSON non validi"}), 400
        callback_custom = data.get("callback", {}).get("custom") if isinstance(data.get("callback"), dict) else None
        if not callback_custom:
            return jsonify({"status": "error", "message": "'callback.custom' mancante nei dati ricevuti"}), 400
        mcp.notify(callback_custom, {
            "type": "callback",
            "payload": data
        })
        return jsonify({"status": "ok"})
except ImportError:
    app = None

def init(request):
    mcp.run(transport="http", host="0.0.0.0", port=8080)
    return mcp(request)

# Entrypoint per Google Cloud Functions
def main(request):
    if app:
        return app(request)
    return "Flask non disponibile", 500

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
