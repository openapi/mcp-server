"""
MCP protocol-level audit logger.

Intercepts JSON-RPC POST bodies and emits a one-line human-readable log entry
for every MCP action without exposing any parameter values (no PII leakage).

Example output:
  [MCP] connect        client=claude-ai/1.0.0
  [MCP] initialized
  [MCP] tools/list
  [MCP] tool call      name=company_search_it
  [MCP] tool call      name=geocoding_reverse
  [MCP] ping           (debug only)
"""

import json
import logging
from starlette.types import ASGIApp, Scope, Receive, Send

_log = logging.getLogger("openapi_mcp_sdk.audit")

# Maps JSON-RPC method → display label (None = suppress at INFO, log at DEBUG only)
_LABELS: dict[str, str | None] = {
    "initialize":                   "connect",
    "notifications/initialized":    "initialized",
    "notifications/cancelled":      "cancelled",
    "notifications/progress":       None,
    "ping":                         None,
    "tools/list":                   "tools/list",
    "tools/call":                   "tool call",
    "resources/list":               "resources/list",
    "resources/read":               "resource read",
    "resources/subscribe":          "resource subscribe",
    "prompts/list":                 "prompts/list",
    "prompts/get":                  "prompt get",
    "completion/complete":          "completion",
    "logging/setLevel":             "set log level",
}


def _emit(body: bytes) -> None:
    """Parse a JSON-RPC body and emit a structured audit log line."""
    try:
        data = json.loads(body)
    except Exception:
        return

    if not isinstance(data, dict) or "method" not in data:
        return

    method: str = data["method"]
    params: dict = data.get("params") or {}
    label = _LABELS.get(method, method)   # unknown methods shown verbatim

    if label is None:
        _log.debug("[MCP] %s", method)
        return

    if method == "initialize":
        info = params.get("clientInfo") or {}
        name    = info.get("name", "unknown")
        version = info.get("version", "")
        proto   = (params.get("protocolVersion") or "")
        _log.info("[MCP] %-18s client=%s/%s  protocol=%s", label, name, version, proto)

    elif method == "tools/call":
        _log.info("[MCP] %-18s name=%s", label, params.get("name", "?"))

    elif method == "resources/read":
        _log.info("[MCP] %-18s uri=%s", label, params.get("uri", "?"))

    elif method == "prompts/get":
        _log.info("[MCP] %-18s name=%s", label, params.get("name", "?"))

    elif method == "notifications/cancelled":
        _log.info("[MCP] %-18s id=%s", label, data.get("id", "?"))

    else:
        _log.info("[MCP] %s", label)


class McpAuditMiddleware:
    """Non-destructive ASGI middleware that logs MCP JSON-RPC calls.

    Wraps the ``receive`` callable to buffer POST body chunks, emits the audit
    log when the body is complete, then replays the original message unchanged
    so the inner app sees an untouched request.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return

        chunks: list[bytes] = []
        done = False

        async def auditing_receive():
            nonlocal done
            message = await receive()
            if message["type"] == "http.request" and not done:
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    done = True
                    _emit(b"".join(chunks))
            return message

        await self.app(scope, auditing_receive, send)
