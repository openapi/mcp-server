import os
import sys
import requests
from fastmcp import FastMCP, Context
from typing import Dict, Any, Optional
from pydantic import BaseModel

# --- Modello Pydantic per Risposte di Errore Standard ---
class ApiError(BaseModel):
    error: str
    message: str

# --- Funzione Helper per Chiamate API ---
def make_api_call(ctx: Context, method: str, url: str, **kwargs) -> Any:
    """
    Funzione helper per estrarre il token e fare la chiamata API.
    """
    # Log avanzato di tutte le proprietà di ctx
    print("[CTX] Proprietà di ctx:")
    for attr in dir(ctx):
        if not attr.startswith('__'):
            try:
                value = getattr(ctx, attr)
                print(f"  ctx.{attr} = {value}")
            except Exception as e:
                print(f"  ctx.{attr} = <errore: {e}>")
    # Log degli headers della richiesta ricevuta dal server
    headers_dict = None
    if hasattr(ctx, 'request_context') and hasattr(ctx.request_context, 'request'):
        headers_dict = ctx.request_context.request.headers
        print("[SERVER] Headers ricevuti nella richiesta:")
        for k, v in headers_dict.items():
            print(f"  {k}: {v}")
    try:
        auth_header = None
        if headers_dict:
            auth_header = headers_dict.get('authorization') or headers_dict.get('Authorization')
        if not auth_header or not auth_header.lower().startswith('bearer '):
            raise ValueError("Header 'Authorization: Bearer <token>' mancante o malformato.")
    except Exception as e:
        return ApiError(error="Auth Error", message=f"Token non fornito dal client: {e}").dict()

    headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as e:
        # Tenta di leggere il corpo della risposta per un messaggio di errore più chiaro
        error_details = e.response.text
        return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").dict()
    except requests.exceptions.RequestException as e:
        return ApiError(error="API Request Error", message=str(e)).dict()

# --- Inizializzazione del Server MCP ---
mcp = FastMCP(
    name="OpenAPI.com Gateway",
    instructions="Questo server fornisce un gateway unificato per diversi servizi di openapi.com."
)

# --- Definizione Manuale dei Tool ---
@mcp.tool
async def get_company_full_profile(vat_or_tax_code: str, ctx: Context) -> Any:
    """
    Recupera il profilo completo e dettagliato di un'azienda italiana 
    fornendo la sua Partita IVA o il suo Codice Fiscale.
    """
    print(f"Esecuzione tool: get_company_full_profile per {vat_or_tax_code}")
    url = f"https://company.openapi.com/IT-full/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def find_cap_by_comune(comune: str, ctx: Context) -> Any:
    """
    Cerca i CAP associati a un dato comune italiano.
    """
    print(f"Esecuzione tool: find_cap_by_comune per {comune}")
    url = "https://cap.openapi.it/cerca_comuni"
    params = {"comune": comune}
    return make_api_call(ctx, "GET", url, params=params)

# --- Puoi aggiungere altri tool per le altre API qui seguendo lo stesso pattern ---

if __name__ == "__main__":
    try:
        print(f"\n--- Server Pronto ---", file=sys.stderr)
        print("Per avviare in modalità remota, eseguire:", file=sys.stderr)
        print("python server.py", file=sys.stderr)
        mcp.run(transport="http", host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"ERRORE AVVIO SERVER: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
