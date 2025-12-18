print("docuengine.py Imported")
from fastmcp import Context
from typing import Any
from src.openapi_mcp_server.mcp_core import make_api_call, mcp, processPolling, getSessionHash
from src.openapi_mcp_server.memory_store import SANDBOX_PREFIX, set_callback_result,callbackUrl



@mcp.tool(
    annotations={
        "title": "Ordinary Company Register - Capital Companies. For Italian companies",
         "readOnlyHint": True,  # Dice all'AI: Questo tool legge dati, non modifica nulla
        "openWorldHint": False, # Dice all'AI: Non puoi inventare parametri a caso
        "idempotentHint": True # Dice all'AI: Se lo chiami 2 volte con gli stessi dati, il risultato è uguale
    }
)
async def post_request_visura_ordinaria(rea: str, ciia_province: str, ctx: Context) -> Any:
    """This endpoint allows you to create a full kyc request on a subject (politically exposed person, adverse media, local politicians, legal enforcement, sanctions, whitelists)    
    	use name for entityType L,W,VE,AC,NA or firstName/lastName for entityType I
    Args:
        rea: rea code of the company
        ciia_province: chamber of commerce Province
    """
    print(f"Running Tool: post_request_visura_ordinaria su rea {rea} per la ciia di {ciia_province}")
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    request_id = getSessionHash(ctx)
    # Serializza il contesto
    custom_context = {
        "request_id": request_id,
        "rea": rea,
        "ciia_province": ciia_province,
    }
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/requests"
    
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": callbackUrl,
            "data": custom_context,
            "method":"JSON",
            "field":"data"
        },
        "headers": {
                "Authorization": auth_header
            },
        "id":"663df75d19a52195e23e315c",
        "field0": rea,
        "field1": ciia_province
    })
    
    print(f"response: {response}")
    state = response.get("stato")

    if state == "wait":
        # Salva subito il risultato parziale per il polling
        set_callback_result(request_id, response, custom_context)
        # avvia un polling ogni secondo su callback_results 
        response = await processPolling(ctx, request_id, ["completed", "success", "DONE"], "stato")
        print(f"response polled: {response}")
        
    return response

