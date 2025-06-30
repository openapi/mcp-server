import os
import sys
import requests
from fastmcp import FastMCP, Context
from typing import Dict, Any, Optional
from pydantic import BaseModel
from mcp_core import mcp, make_api_call

# --- Modello Pydantic per Risposte di Errore Standard ---
class ApiError(BaseModel):
    error: str
    message: str

# --- Funzione Helper per Chiamate API ---
# def make_api_call(ctx: Context, method: str, url: str, json_payload: Optional[dict] = None, **kwargs) -> Any:
#     """
#     Funzione helper per estrarre il token e fare la chiamata API.
#     Accetta opzionalmente un payload JSON.
#     """
#     print(f"Call api url: {url}")
#     for attr in dir(ctx):
#         if not attr.startswith('__'):
#             try:
#                 value = getattr(ctx, attr)
#             except Exception as e:
#                 print(f"  ctx.{attr} = <errore: {e}>")
#     headers_dict = None
#     if hasattr(ctx, 'request_context') and hasattr(ctx.request_context, 'request'):
#         headers_dict = ctx.request_context.request.headers
#     try:
#         auth_header = None
#         if headers_dict:
#             auth_header = headers_dict.get('authorization') or headers_dict.get('Authorization')
#         if not auth_header or not auth_header.lower().startswith('bearer '):
#             raise ValueError("Header 'Authorization: Bearer <token>' mancante o malformato.")
#     except Exception as e:
#         return ApiError(error="Auth Error", message=f"Token non fornito dal client: {e}").dict()

#     headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}
#     try:
#         request_args = dict(method=method, url=url, headers=headers, **kwargs)
#         if json_payload is not None:
#             request_args["json"] = json_payload
#         response = requests.request(**request_args)
#         response.raise_for_status()
#         return response.json().get('data', {})
#     except requests.exceptions.HTTPError as e:
#         # Tenta di leggere il corpo della risposta per un messaggio di errore più chiaro
#         error_details = e.response.text
#         return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").dict()
#     except requests.exceptions.RequestException as e:
#         return ApiError(error="API Request Error", message=str(e)).dict()

# --- Inizializzazione del Server MCP ---
# mcp = FastMCP(
#     name="OpenAPI.com Gateway",
#     instructions="Questo server fornisce un gateway unificato per diversi servizi di openapi.com."
# )

# --- Importa i tool ---
from apis import company, cap, trust, visurecamerali, sms

def init(request):
    return mcp(request)

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
