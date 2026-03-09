print("exchange.py Imported")
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp, getSessionHash
from ..memory_store import SANDBOX_PREFIX

@mcp.tool
async def get_today_exchange_rates(ctx: Context) -> Any:
    """Obtain daily world exchange rate based on USD value
    """
    print(f"Running Tool: getTodayExchangeRates")
    url = f"https://{SANDBOX_PREFIX}exchange.altravia.com/"
    session_hash = getSessionHash(ctx)
    print(f"session_hash: {session_hash}") 
    api_call = make_api_call(ctx, "GET", url)
    
    return api_call
