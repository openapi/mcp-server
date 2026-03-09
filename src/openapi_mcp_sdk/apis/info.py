import logging
logging.getLogger(__name__).debug("module loaded")
from ..mcp_core import mcp, getSessionHash
from ..memory_store import BASE_URL, SANDBOX_PREFIX
from fastmcp import Context
from typing import Any
import sys
import os
import socket
import platform
from datetime import datetime, timezone

# All instance identity fields are captured once at startup.
# Each running process (local dev, staging, Cloud Run) will show
# different values, making instances distinguishable at a glance.
_SERVER_START    = datetime.now(timezone.utc)
_INSTANCE_HOST   = socket.gethostname()
_INSTANCE_USER   = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
_INSTANCE_PID    = os.getpid()
# Human-readable label: "alice@macbook-pro" locally, pod name on k8s/Cloud Run
_INSTANCE_LABEL  = f"{_INSTANCE_USER}@{_INSTANCE_HOST}"

try:
    from importlib.metadata import version as _pkg_version
    _FASTMCP_VERSION = _pkg_version("fastmcp")
except Exception:
    _FASTMCP_VERSION = "unknown"

_SERVER_VERSION = "0.2.0"
_SERVER_NAME    = "OpenAPI.com MCP Gateway"


def _mask_token(token: str) -> str:
    """Show only the first 8 and last 4 chars; mask the rest."""
    if len(token) <= 12:
        return token[:4] + "..." + token[-2:]
    return token[:8] + "..." + token[-4:]


@mcp.tool
async def openapi_server_info(ctx: Context) -> Any:
    """
    Call this tool whenever the user asks:
    - "are you connected to openapi?" / "sei connesso a openapi?"
    - "which server / instance is running?"
    - "what is your status?" / "are the tools working?"
    - any question about connectivity, health, or identity of this MCP server.

    Returns live diagnostic data directly from the running process — no external
    API calls are made. The response includes:
    - server name, version, and mode (sandbox vs production)
    - instance identity: user@hostname, PID, and startup timestamp so different
      running instances (local dev, staging, Cloud Run) are immediately distinguishable
    - token status: whether OPENAPI_TOKEN / OPENAPI_SANDBOX_TOKEN are set in the
      server environment, with a masked preview of the active token
    - list of all MCP tools currently registered and available
    - session identifiers for the current request
    """
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - _SERVER_START).total_seconds())

    sandbox_mode = bool(SANDBOX_PREFIX)

    # Token presence and masked preview — never expose the full token
    prod_token    = os.environ.get("OPENAPI_TOKEN", "")
    sandbox_token = os.environ.get("OPENAPI_SANDBOX_TOKEN", "")
    token_info = {
        "OPENAPI_TOKEN":         "set" if prod_token    else "not set",
        "OPENAPI_SANDBOX_TOKEN": "set" if sandbox_token else "not set",
        "active_token_preview":  _mask_token(sandbox_token if sandbox_mode else prod_token)
                                 if (sandbox_token if sandbox_mode else prod_token) else None,
    }

    # Collect registered tool names from the MCP instance
    try:
        tool_names = sorted(t.name for t in await mcp.list_tools())
    except Exception:
        tool_names = []

    return {
        "server": {
            "name":        _SERVER_NAME,
            "version":     _SERVER_VERSION,
            "mode":        "sandbox" if sandbox_mode else "production",
            "base_url":    BASE_URL,
            "description": mcp.instructions,
        },
        "instance": {
            "label":      _INSTANCE_LABEL,
            "host":       _INSTANCE_HOST,
            "user":       _INSTANCE_USER,
            "pid":        _INSTANCE_PID,
            "started_at": _SERVER_START.isoformat(),
        },
        "token": token_info,
        "runtime": {
            "python":   sys.version,
            "platform": platform.platform(),
            "fastmcp":  _FASTMCP_VERSION,
        },
        "uptime": {
            "started_at":     _SERVER_START.isoformat(),
            "checked_at":     now.isoformat(),
            "uptime_seconds": uptime_seconds,
        },
        "session": {
            "request_id":   ctx.request_id,
            "session_id":   ctx.session_id,
            "client_id":    ctx.client_id or "unknown",
            "session_hash": getSessionHash(ctx),
        },
        "tools": {
            "count": len(tool_names),
            "names": tool_names,
        },
        "status": "ok",
    }
