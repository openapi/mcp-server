print("info.py Imported")
from src.openapi_mcp_server.mcp_core import mcp, getSessionHash
from src.openapi_mcp_server.memory_store import BASE_URL, SANDBOX_PREFIX
from fastmcp import Context
from typing import Any
import sys
import os
import platform
from datetime import datetime, timezone

# Recorded at import time so uptime can be computed
_SERVER_START = datetime.now(timezone.utc)

try:
    from importlib.metadata import version as _pkg_version
    _FASTMCP_VERSION = _pkg_version("fastmcp")
except Exception:
    _FASTMCP_VERSION = "unknown"

_SERVER_VERSION = "0.2.0"
_SERVER_NAME    = "OpenAPI.com MCP Gateway"


@mcp.tool
async def openapi_server_info(ctx: Context) -> Any:
    """
    Returns diagnostic information about this MCP server instance.
    Use this tool to verify that the MCP server is reachable and correctly configured.
    No external API calls are made — all data comes from the running process itself.
    """
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - _SERVER_START).total_seconds())

    sandbox_mode = bool(SANDBOX_PREFIX)

    # Collect registered tool names from the MCP instance
    try:
        tool_names = sorted(t.name for t in await mcp.list_tools())
    except Exception:
        tool_names = []

    return {
        "server": {
            "name":    _SERVER_NAME,
            "version": _SERVER_VERSION,
            "mode":    "sandbox" if sandbox_mode else "production",
            "base_url": BASE_URL,
        },
        "runtime": {
            "python":  sys.version,
            "platform": platform.platform(),
            "fastmcp": _FASTMCP_VERSION,
        },
        "uptime": {
            "started_at":     _SERVER_START.isoformat(),
            "checked_at":     now.isoformat(),
            "uptime_seconds": uptime_seconds,
        },
        "session": {
            "request_id": ctx.request_id,
            "session_id": ctx.session_id,
            "client_id":  ctx.client_id or "unknown",
            "session_hash": getSessionHash(ctx),
        },
        "tools": {
            "count": len(tool_names),
            "names": tool_names,
        },
        "status": "ok",
    }
