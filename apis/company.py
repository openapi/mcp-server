print("company.py importato")
from memory_store import callback_results,localDomain  # usa sempre il singleton globale
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp
import asyncio
import pprint


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
    
    # Usa un request_id
    request_id = ctx.request_id
    
    # Serializza il contesto
    custom_context = {
        "request_id": request_id,
        "vat_or_taxCode": vat_or_taxCode
    }
    url = f"https://company.openapi.com/IT-full/{vat_or_taxCode}"
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": "https://"+localDomain+"/callbacks",
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
    state = response.get("state")
    
    if state == "PENDING":
        # Salva subito il risultato parziale per il polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # avvia un polling ogni secondo su callback_results 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            company_name = None
            if result:
                res = result.get("result")
                if res:
                    details = res.get("companyDetails")
                    if details:
                        company_name = details.get("companyName")
            if company_name is not None:
                response = res
                break
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
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

