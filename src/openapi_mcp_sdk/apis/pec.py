import logging
logging.getLogger(__name__).debug("module loaded")
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp
from ..memory_store import OPENAPI_HOST_PREFIX


@mcp.tool(
    annotations={
        "title": "Certified email address availability check",
        "readOnlyHint": True,  # Tells the AI: this tool only reads data, it does not modify anything
        "openWorldHint": False, # Tells the AI: do not invent arbitrary parameter values
        "idempotentHint": False # Tells the AI: calling twice with the same input yields the same result
    }
)

async def check_pec(pec: str, ctx: Context) -> Any:
    """
    Checks if a specific PEC (Certified Email) address is available for purchase
    Use this tool when the user asks if a PEC address is avaible
         
    Args:
        pec: the pec address to check
    """  
    
    url = f"https://{OPENAPI_HOST_PREFIX}pec.openapi.it/verifica_pec/{pec}"
    return make_api_call(ctx, "GET", url)
