print("visurecamerali.py importato")
from memory_store import set_callback_result,callbackUrl  # usa sempre il singleton globale
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp, processPolling

@mcp.tool
async def get_italian_company_official_documents_list(vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Recupera un elenco di endpoint di visure camerali disponibili per una azienda da usare con il tool get_italian_company_official_document
    fornendo la sua Partita IVA o il suo Codice Fiscale.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    print(f"Esecuzione tool: get_official_documents_list per {vat_or_tax_code}")
    url = f"https://visurecamerali.openapi.it/impresa/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def get_italian_company_official_document(document_url:str,vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Recupera una visura camerale di una azienda fornendo la sua Partita IVA o il suo Codice Fiscale.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    print(f"Esecuzione tool: get_italian_company_official_document su {document_url} per {vat_or_tax_code}")
    url = f"https://{document_url}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    # Usa un request_id
    request_id = ctx.request_id
    # Serializza il contesto
    custom_context = {
        "request_id": request_id,
        "document_url": document_url,
        "vat_or_tax_code": vat_or_tax_code,
    }
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": callbackUrl,
            "data": custom_context,
            "method":"JSON",
            "field":"data"
        },
        "cf_piva_id":vat_or_tax_code
    })
    state = response.get("stato_richiesta")
    
    if state == "In erogazione":
        # Salva subito il risultato parziale per il polling
        set_callback_result(request_id, response, custom_context)
        # avvia un polling ogni secondo su callback_results 
        response =  await processPolling(ctx, request_id, ["Visura evasa"],"stato_richiesta")
        if response.get("result").get("stato_richiesta") == "Visura evasa":
                response = make_api_call(ctx, "GET", url+"/"+response.get("result").get("id")+"/allegati")
    return response
       