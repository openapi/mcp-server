print("pec.py Imported")
from fastmcp import Context
from typing import Any
from src.openapi_mcp_server.mcp_core import make_api_call, mcp
from src.openapi_mcp_server.memory_store import SANDBOX_PREFIX


@mcp.tool(
    annotations={
        "title": "Certified email address availability check",
        "readOnlyHint": True,  # Dice all'AI: Questo tool legge dati, non modifica nulla
        "openWorldHint": False, # Dice all'AI: Non puoi inventare parametri a caso
        "idempotentHint": False # Dice all'AI: Se lo chiami 2 volte con gli stessi dati, il risultato è uguale
    }
)

async def check_pec(pec: str, ctx: Context) -> Any:
    """
    Checks if a specific PEC (Certified Email) address is available for purchase
    Use this tool when the user asks if a PEC address is avaible
         
    Args:
        pec: the pec address to check
    """  
    
    url = f"https://{SANDBOX_PREFIX}pec.openapi.it/verifica_pec/{pec}"
    return make_api_call(ctx, "GET", url)