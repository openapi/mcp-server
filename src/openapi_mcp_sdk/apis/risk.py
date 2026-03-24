import logging
logging.getLogger(__name__).debug("module loaded")
from ..memory_store import set_callback_result, callbackUrl, OPENAPI_HOST_PREFIX  # usa sempre il singleton globale
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp, processPolling, getSessionHash
import asyncio


@mcp.tool(
    annotations={
        "title": "Full Worldwide KYC FULL",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def post_risk_WW_kyc_full(firstName: str,lastName: str,entityType: str,name: str, ctx: Context) -> Any:
    """This endpoint allows you to create a full kyc request on a subject (politically exposed person, adverse media, local politicians, legal enforcement, sanctions, whitelists)    
    	use name for entityType L,W,VE,AC,NA or firstName/lastName for entityType I
    Args:
        firstName: first name of the person
        lastName: lastName of the person
        entityType: can be I=Individual,L=Legal Entity,W=Website,VE=Vessel,AC=Aircraft,NA=Unknown
        name: the name of the entity if not Individual
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = getSessionHash(ctx)
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "firstName": firstName,
        "lastName": lastName,
        "entityType": entityType,
        "name": name,
    }
    url = f"https://{OPENAPI_HOST_PREFIX}risk.openapi.com/WW-kyc-full"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    if firstName:
        json_payload["firstname"] = {"value": firstName}
    if lastName:
        json_payload["lastName"] = {"value": lastName}
    if entityType:
        json_payload["entityType"] = {"value": entityType}
    if name:
        json_payload["name"] = {"value": name}
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        set_callback_result(request_id, response, custom_context)
        # Poll callback_results once per second 
        response =  await processPolling(ctx, request_id, ["DONE"])
    return response

@mcp.tool(
    annotations={
        "title": "Provides detailed credit score information for a specific organization using a tax code, VAT number",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_risk_IT_creditscore_top(vat_or_taxCode: str, ctx: Context) -> Any:
    """Returns Operational credit limits, Rating evaluations, Risk score history, Public ratings, Financial positions and profiles
        of an italian company from vatCode or taxCode.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    url = f"https://{OPENAPI_HOST_PREFIX}risk.openapi.com/IT-creditscore-top/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool(
    annotations={
        "title": "Check if Italian Fiscal Code is real and existent in the official database",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_IT_fiscal_code(fiscalCode: str, ctx: Context) -> Any:
    """Check if an Italian Fiscal Code is real and existent in the official database.
    Args:
        fiscalCode: fiscal code of an italian person
    """
    url = f"https://{OPENAPI_HOST_PREFIX}risk.openapi.com/IT-verifica_cf/{fiscalCode}"
    return make_api_call(ctx, "GET", url)
