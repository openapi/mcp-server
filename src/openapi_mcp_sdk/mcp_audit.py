"""
MCP protocol-level audit logger.

Intercepts JSON-RPC POST bodies and emits a one-line human-readable log entry
for every MCP action without exposing any parameter values (no PII leakage).

Example output:
  [MCP] connect        ip=1.2.3.4  client=claude-ai/1.0.0
  [MCP] initialized    ip=1.2.3.4
  [MCP] tools/list     ip=1.2.3.4
  [MCP] tool call      ip=1.2.3.4  name=company_search_it
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


def _emit(body: bytes, client_ip: str) -> None:
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
        _log.debug("[MCP] %s  ip=%s", method, client_ip)
        return

    if method == "initialize":
        info = params.get("clientInfo") or {}
        name    = info.get("name", "unknown")
        version = info.get("version", "")
        proto   = (params.get("protocolVersion") or "")
        _log.info("[MCP] %-18s ip=%-15s client=%s/%s  protocol=%s", label, client_ip, name, version, proto)

    elif method == "tools/call":
        _log.info("[MCP] %-18s ip=%-15s name=%s", label, client_ip, params.get("name", "?"))

    elif method == "resources/read":
        _log.info("[MCP] %-18s ip=%-15s uri=%s", label, client_ip, params.get("uri", "?"))

    elif method == "prompts/get":
        _log.info("[MCP] %-18s ip=%-15s name=%s", label, client_ip, params.get("name", "?"))

    elif method == "notifications/cancelled":
        _log.info("[MCP] %-18s ip=%-15s id=%s", label, client_ip, data.get("id", "?"))

    else:
        _log.info("[MCP] %-18s ip=%s", label, client_ip)


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

        client = scope.get("client") or ("?", 0)
        client_ip: str = client[0]

        chunks: list[bytes] = []
        done = False

        async def auditing_receive():
            nonlocal done
            message = await receive()
            if message["type"] == "http.request" and not done:
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    done = True
                    _emit(b"".join(chunks), client_ip)
            return message

        await self.app(scope, auditing_receive, send)
