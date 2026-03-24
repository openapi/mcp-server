import logging
logging.getLogger(__name__).debug("module loaded")
from fastmcp import Context
from typing import Any
from ..mcp_core import mcp
from ..memory_store import get_callback_result

logger = logging.getLogger(__name__)

@mcp.tool
async def check_async_status(request_id: str, ctx: Context) -> Any:
    """Show the last status of an async request
    Args:
        request_id: required, returned by an async downgraded request to the mcp server
    """
    return get_callback_result(request_id)
