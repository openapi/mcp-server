print("trust.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def checkEmailStart(email: str, ctx: Context) -> Any:
    """
    Recupera informazioni dettagliate su un indirizzo email (spf,dmark,disposability,frauds)
    """
    print(f"Esecuzione tool: checkEmailBase per {email}")
    url = f"https://trust.openapi.com/email-start/{email}"
    return make_api_call(ctx, "POST", url, json_payload={})
@mcp.tool
async def checkMobileStart(mobileNumber: str, ctx: Context) -> Any:
    """
    Recupera informazioni dettagliate su un numero di cellulare (isPossible,isValid,regionCode,isValidNumberForRegion,network,originalNetwork,roaming,ported,country)"
    """
    print(f"Esecuzione tool: checkMobileStart per {mobileNumber}")
    url = f"https://trust.openapi.com/mobile-start/{mobileNumber}"
    return make_api_call(ctx, "POST", url,json_payload={})