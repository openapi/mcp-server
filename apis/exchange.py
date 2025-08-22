print("exchange.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def getTodayExchangeRates(ctx: Context) -> Any:
    """Obtain world exchange rate based on USD value
    """
    print(f"Esecuzione tool: getTodayExchangeRates")
    
    url = f"https://exchange.altravia.com/"
    api_call =  make_api_call(ctx, "GET", url)
    return api_call
