"""Tests for TokenQuerystringMiddleware auth conflict handling.

These tests use a minimal ASGI setup to test the middleware in isolation,
avoiding the full FastAPI/MCP stack. Requires Python 3.13+ and project deps.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def middleware():
    """Import and instantiate TokenQuerystringMiddleware with a mock inner app."""
    from openapi_mcp_sdk.main import TokenQuerystringMiddleware

    inner_app = AsyncMock()
    return TokenQuerystringMiddleware(inner_app), inner_app


@pytest.fixture
def base_scope():
    """Return a minimal HTTP scope dict."""
    return {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
    }


def _header_bytes(headers: list[tuple[str, str]]) -> list[tuple[bytes, bytes]]:
    """Convert string header tuples to bytes as ASGI expects."""
    return [(k.encode(), v.encode()) for k, v in headers]


class TestTokenQuerystringMiddleware:
    """Tests for TokenQuerystringMiddleware behavior."""

    @pytest.mark.asyncio
    async def test_query_token_only_sets_auth_header(self, middleware, base_scope):
        """When only ?token= is provided, it should be promoted to Authorization header."""
        mw, inner_app = middleware
        base_scope["query_string"] = b"token=my-token"

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        # Should call inner app, not short-circuit
        inner_app.assert_called_once()
        call_scope = inner_app.call_args[0][0]
        headers_dict = {k.decode(): v.decode() for k, v in call_scope["headers"]}
        assert headers_dict.get("authorization") == "Bearer my-token"
        # Query string should be cleaned
        assert call_scope["query_string"] == b""

    @pytest.mark.asyncio
    async def test_header_only_passes_through(self, middleware, base_scope):
        """When only Authorization header is provided, middleware should pass it through unchanged."""
        mw, inner_app = middleware
        base_scope["headers"] = _header_bytes([("Authorization", "Bearer header-token")])

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        inner_app.assert_called_once()
        call_scope = inner_app.call_args[0][0]
        headers_dict = {k.decode(): v.decode() for k, v in call_scope["headers"]}
        assert headers_dict.get("authorization") == "Bearer header-token"

    @pytest.mark.asyncio
    async def test_conflicting_auth_returns_400(self, middleware, base_scope):
        """When both ?token= and Authorization header are present, return 400."""
        mw, inner_app = middleware
        base_scope["query_string"] = b"token=query-token"
        base_scope["headers"] = _header_bytes([("Authorization", "Bearer header-token")])

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        # Should NOT call inner app — middleware short-circuits
        inner_app.assert_not_called()

        # Verify 400 response was sent
        calls = send.call_args_list
        assert len(calls) == 2

        start_msg = calls[0][0][0]
        assert start_msg["type"] == "http.response.start"
        assert start_msg["status"] == 400

        body_msg = calls[1][0][0]
        assert body_msg["type"] == "http.response.body"
        body = json.loads(body_msg["body"])
        assert body["error"] == "conflicting_auth"
        assert "Authorization header" in body["message"]
        assert "?token=" in body["message"]

    @pytest.mark.asyncio
    async def test_conflicting_auth_response_is_json(self, middleware, base_scope):
        """The 400 response for conflicting auth should have application/json content-type."""
        mw, inner_app = middleware
        base_scope["query_string"] = b"token=a"
        base_scope["headers"] = _header_bytes([("Authorization", "Bearer b")])

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        start_msg = send.call_args_list[0][0][0]
        headers = {k: v for k, v in start_msg["headers"]}
        assert b"application/json" == headers.get(b"content-type")

    @pytest.mark.asyncio
    async def test_no_auth_passes_through(self, middleware, base_scope):
        """When no auth is provided, middleware should pass through without error."""
        mw, inner_app = middleware

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        inner_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_http_scope_passes_through(self, middleware, base_scope):
        """Non-HTTP scopes (e.g., websocket) should pass through unchanged."""
        mw, inner_app = middleware
        scope = {"type": "websocket"}

        receive = AsyncMock()
        send = AsyncMock()
        await mw(scope, receive, send)

        inner_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_query_token_with_other_params_preserved(self, middleware, base_scope):
        """When ?token= is present with other params, only token should be removed."""
        mw, inner_app = middleware
        base_scope["query_string"] = b"token=my-token&foo=bar&baz=qux"

        receive = AsyncMock()
        send = AsyncMock()
        await mw(base_scope, receive, send)

        call_scope = inner_app.call_args[0][0]
        qs = call_scope["query_string"].decode()
        assert "token=" not in qs
        assert "foo=bar" in qs
        assert "baz=qux" in qs
