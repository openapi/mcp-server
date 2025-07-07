print("trust.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp
import json

@mcp.tool
def checkEmailStart(email: str, ctx: Context) -> Any:
    """
    Retrieves detailed information about an email address (spf, dmark, disposability, frauds)
    """
    print(f"Esecuzione tool: checkEmailBase per {email}")
    url = f"https://trust.openapi.com/email-start/{email}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    # Serializza il contesto
    custom_context = json.dumps({
        "client_id": ctx.client_id,
        "email": email
    })
    # Qui puoi generare un request_id unico se vuoi tracciare più richieste per client
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": "https://dev.mcp.openapi.com/callbacks/",
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
    # Correggi l'accesso ai dati
    state = response.get("state") or response.get("data", {}).get("state")
    if state == "DONE":
        return response.get("result") or response
    elif state in ("WAIT", "NEW", "PENDING"):
        return {
            "state": "PENDING",
            "client_id": ctx.client_id,
            "poll_url": f"/status/{ctx.client_id}",
            "message": "Elaborazione in corso, eseguire polling su /status/{client_id}"
        }
    else:
        return response
@mcp.tool
async def checkMobileStart(mobileNumber: str, ctx: Context) -> Any:
    """
    Retrieves detailed information about a mobile number (isPossible, isValid, regionCode, isValidNumberForRegion, network, originalNetwork, roaming, ported, country)
    """
    print(f"Esecuzione tool: checkMobileStart per {mobileNumber}")
    url = f"https://trust.openapi.com/mobile-start/{mobileNumber}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    # Serializza il contesto
    custom_context = json.dumps({
        "client_id": ctx.client_id,
        "mobileNumber": mobileNumber
    })
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": "https://dev.mcp.openapi.com/callbacks/",
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
    state = response.get("state") or response.get("data", {}).get("state")
    if state == "DONE":
        return response.get("result") or response
    elif state in ("WAIT", "NEW", "PENDING"):
        return {
            "state": "PENDING",
            "client_id": ctx.client_id,
            "poll_url": f"/status/{ctx.client_id}",
            "message": "Elaborazione in corso, eseguire polling su /status/{client_id}"
        }
    else:
        return response
