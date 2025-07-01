print("trust.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def checkEmailStart(email: str, ctx: Context) -> Any:
    """
    Retrieves detailed information about an email address (spf, dmark, disposability, frauds)
    """
    print(f"Esecuzione tool: checkEmailBase per {email}")
    url = f"https://trust.openapi.com/email-start/{email}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    return make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": "https://mcp.openapi.com/callbacks/",
            "custom": ctx.client_id,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
@mcp.tool
async def checkMobileStart(mobileNumber: str, ctx: Context) -> Any:
    """
    Retrieves detailed information about a mobile number (isPossible, isValid, regionCode, isValidNumberForRegion, network, originalNetwork, roaming, ported, country)
    """
    print(f"Esecuzione tool: checkMobileStart per {mobileNumber}")
    url = f"https://trust.openapi.com/mobile-start/{mobileNumber}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    return make_api_call(ctx, "POST", url,json_payload={
        "callback": {
            "url": "https://mcp.openapi.com/callbacks/",
            "custom": ctx.client_id,
            "headers": {
                "Authorization": auth_header
            }
        }
    })