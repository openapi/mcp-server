print("exchange.py importato")
from fastmcp import Context
from typing import Any
from src.openapi_mcp_server.mcp_core import make_api_call, mcp, getSessionHash
from src.openapi_mcp_server.memory_store import SANDBOX_PREFIX

@mcp.tool
async def get_today_exchange_rates(ctx: Context) -> Any:
    """Obtain daily world exchange rate based on USD value
    """
    print(f"Esecuzione tool: getTodayExchangeRates")
    url = f"https://{SANDBOX_PREFIX}exchange.altravia.com/"
    session_hash = getSessionHash(ctx)
    print(f"session_hash: {session_hash}") 
    api_call = make_api_call(ctx, "GET", url)
    
    return api_call
