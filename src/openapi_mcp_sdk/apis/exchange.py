import logging
logging.getLogger(__name__).debug("module loaded")
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp
from ..memory_store import SANDBOX_PREFIX

logger = logging.getLogger(__name__)

@mcp.tool
async def get_today_exchange_rates(ctx: Context) -> Any:
    """Obtain daily world exchange rate based on USD value
    """
    url = f"https://{SANDBOX_PREFIX}exchange.altravia.com/"
    return make_api_call(ctx, "GET", url)
