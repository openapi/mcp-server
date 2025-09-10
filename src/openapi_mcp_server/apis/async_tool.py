print("async_tool.py Imported")
from fastmcp import Context
from typing import Any
from src.openapi_mcp_server.mcp_core import mcp
from src.openapi_mcp_server.memory_store import get_callback_result

@mcp.tool
async def check_async_status(request_id: str, ctx: Context) -> Any:
    """Show the last status of an async request
    Args:
        request_id: required, returned by an async downgraded request to the mcp server
    """
    print(f"Running Tool: check_async_status {request_id}")
    
    return get_callback_result(request_id)