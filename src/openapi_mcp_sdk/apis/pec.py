"""PEC tools."""

import logging
from typing import Any

from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import make_api_call, mcp
from ..memory_store import OPENAPI_HOST_PREFIX

logging.getLogger(__name__).debug("module loaded")


@mcp.tool(
    annotations={
        "title": "Certified email address availability check",
        "readOnlyHint": True,  # This tool only reads data.
        "openWorldHint": False,  # Do not invent arbitrary parameter values.
        "idempotentHint": False,  # The same input yields the same result.
    }
)
async def check_pec(pec: str, ctx: Context) -> Any:
    """
    Checks if a specific PEC (Certified Email) address is available.

    Use this tool when the user asks if a PEC address is available.

    Args:
        pec: the pec address to check
    """

    url = f"https://{OPENAPI_HOST_PREFIX}pec.openapi.it/verifica_pec/{pec}"
    return make_api_call(ctx, "GET", url)
