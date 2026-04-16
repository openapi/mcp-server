"""Risk tools."""

import logging
from typing import Any

# MCP tool names and parameter names intentionally mirror the public API.
# pylint: disable=invalid-name
from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import getSessionHash, make_api_call, mcp, processPolling
from ..memory_store import OPENAPI_HOST_PREFIX, callbackUrl, set_callback_result

logging.getLogger(__name__).debug("module loaded")


@mcp.tool(
    annotations={"title": "Full Worldwide KYC FULL", "readOnlyHint": True, "openWorldHint": False, "idempotentHint": True}
)
async def post_risk_WW_kyc_full(
    firstName: str,
    lastName: str,
    entityType: str,
    name: str,
    ctx: Context,
) -> Any:
    """Create a full KYC request on a subject.

    Covers politically exposed persons, adverse media, local politicians,
    legal enforcement, sanctions, and whitelists.
    Use ``name`` for entity types ``L``, ``W``, ``VE``, ``AC``, ``NA`` or
    ``firstName`` and ``lastName`` for entity type ``I``.

    Args:
        firstName: first name of the person
        lastName: lastName of the person
        entityType: one of I, L, W, VE, AC, or NA
        name: the name of the entity if not Individual
    """
    auth_header = ctx.request_context.request.headers.get("authorization") or ctx.request_context.request.headers.get(
        "Authorization"
    )

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
    json_payload = {"callback": {"url": callbackUrl, "custom": custom_context, "headers": {"Authorization": auth_header}}}
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
        response = await processPolling(ctx, request_id, ["DONE"])
    return response


@mcp.tool(
    annotations={
        "title": "Provides detailed credit score information for a specific organization using a tax code, VAT number",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True,
    }
)
async def get_risk_IT_creditscore_top(vat_or_taxCode: str, ctx: Context) -> Any:
    """Returns detailed credit score information for an Italian company.

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
        "idempotentHint": True,
    }
)
async def check_IT_fiscal_code(fiscalCode: str, ctx: Context) -> Any:
    """Check if an Italian Fiscal Code is real and existent in the official database.
    Args:
        fiscalCode: fiscal code of an italian person
    """
    url = f"https://{OPENAPI_HOST_PREFIX}risk.openapi.com/IT-verifica_cf/{fiscalCode}"
    return make_api_call(ctx, "GET", url)
