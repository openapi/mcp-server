"""
MCP protocol-level audit logger.

Intercepts JSON-RPC POST bodies and emits a one-line human-readable log entry
for every MCP action without exposing any parameter values (no PII leakage).

Uniform layout across all log lines:
  [TAG]              IP "Action" key=value
  [MCP]              X.X.X.X "Connect" client=claude-ai/1.0.0 protocol=2025-11-25
  [MCP]              X.X.X.X "Tool call" name=company_search_it
  [MCP]              X.X.X.X "Tools list"
"""

import json
import logging
from starlette.types import ASGIApp, Scope, Receive, Send  # pylint: disable=import-error

_log = logging.getLogger("openapi_mcp_sdk.audit")

# Maps JSON-RPC method → display label (None = suppress at INFO, log at DEBUG only)
_LABELS: dict[str, str | None] = {
    "initialize":                   "Connect",
    "notifications/initialized":    "Initialized",
    "notifications/cancelled":      "Cancelled",
    "notifications/progress":       None,
    "ping":                         None,
    "tools/list":                   "Tools list",
    "tools/call":                   "Tool call",
    "resources/list":               "Resources list",
    "resources/read":               "Resource read",
    "resources/subscribe":          "Resource subscribe",
    "prompts/list":                 "Prompts list",
    "prompts/get":                  "Prompt get",
    "completion/complete":          "Completion",
    "logging/setLevel":             "Set log level",
}

_TAG = "[MCP]"


def _emit(body: bytes, client_ip: str) -> None:
    """Parse a JSON-RPC body and emit a structured audit log line."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return

    if not isinstance(data, dict) or "method" not in data:
        return

    method: str = data["method"]
    params: dict = data.get("params") or {}
    label = _LABELS.get(method, method.capitalize())

    if label is None:
        _log.debug('%s %s "%s"', _TAG, client_ip, method)
        return

    if method == "initialize":
        info = params.get("clientInfo") or {}
        name    = info.get("name", "unknown")
        version = info.get("version", "")
        proto   = (params.get("protocolVersion") or "")
        _log.info('%s %s "Connect" client=%s/%s protocol=%s', _TAG, client_ip, name, version, proto)

    elif method == "tools/call":
        _log.info('%s %s "Tool call" name=%s', _TAG, client_ip, params.get("name", "?"))

    elif method == "resources/read":
        _log.info('%s %s "Resource read" uri=%s', _TAG, client_ip, params.get("uri", "?"))

    elif method == "prompts/get":
        _log.info('%s %s "Prompt get" name=%s', _TAG, client_ip, params.get("name", "?"))

    elif method == "notifications/cancelled":
        _log.info('%s %s "Cancelled" id=%s', _TAG, client_ip, data.get("id", "?"))

    else:
        _log.info('%s %s "%s"', _TAG, client_ip, label)


class McpAuditMiddleware:  # pylint: disable=too-few-public-methods
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
