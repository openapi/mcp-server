print("company.py importato")
from memory_store import callback_results  # usa sempre il singleton globale
from pydantic import BaseModel
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp
import json
import uuid


@mcp.tool(
    annotations={
        "title": "Full company data from VAT",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_IT_full(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo completo e dettagliato di un'azienda italiana dato Partita IVA o Codice Fiscale.    

    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un client_id generato se ctx.client_id è None
    client_id = ctx.client_id or str(uuid.uuid4())
    # Serializza il contesto
    custom_context = {
        "client_id": client_id,
        "vat_or_taxCode": vat_or_taxCode
    }
    url = f"https://company.openapi.com/IT-full/{vat_or_taxCode}"
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": "https://dev.mcp.openapi.com/callbacks",
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
    state = response.get("state")
    if state in ("PENDING"):
        # Costruisci poll_url assoluto
        poll_url = f"https://dev.mcp.openapi.com/status/{client_id}"
        # Salva subito il risultato parziale per il polling
        callback_results[client_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }
        return {
            "state": "PENDING",
            "client_id": client_id,
            "poll_url": poll_url,
            "message": "Elaborazione in corso, eseguire polling su /status/{client_id}"
        }
    print("DEBUG ctx.client_id:", ctx.client_id, "| client_id usato:", client_id)
    print(response)
    return response

@mcp.tool
async def get_company_IT_advanced(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo avanzato di un'azienda italiana dato Partita IVA o Codice Fiscale."""
    url = f"https://company.openapi.com/IT-advanced/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def get_company_IT_base(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo base di un'azienda italiana dato Partita IVA o Codice Fiscale."""
    url = f"https://company.openapi.com/IT-start/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def get_company_IT_search(companyName: str, ctx: Context) -> Any:
    """Restituisce un elenco di aziende italiane dato il nome o parte di esso."""
    url = f"https://company.openapi.com/IT-search?companyName={companyName}&limit=10&dataEnrichment=name"
    return make_api_call(ctx, "GET", url)

