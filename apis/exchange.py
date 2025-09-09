print("exchange.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp, getSessionHash

@mcp.tool
async def get_today_exchange_rates(ctx: Context) -> Any:
    """Obtain daily world exchange rate based on USD value
    """
    print(f"Esecuzione tool: getTodayExchangeRates")
    url = f"https://exchange.altravia.com/"
    session_hash = getSessionHash(ctx)
    print(f"session_hash: {session_hash}") 
    api_call = make_api_call(ctx, "GET", url)
    
    return api_call
