# FastMCP Session Management

Reference for tracking client sessions and managing per-session state in FastMCP servers.

FastMCP does not expose a `get_context_by_client_id` method. Session state must be
managed explicitly using the identifiers available on `Context`.

---

## Context identifiers

| Field | Available on | Description |
|---|---|---|
| `ctx.session_id` | HTTP transports | Stable across requests in the same session |
| `ctx.client_id` | all transports | Client identifier (may be `None`) |
| `ctx.request_id` | all transports | Unique per request, use as fallback key |

**Important constraints:**
- `Context` objects are bound to a single request lifecycle and must not be stored or shared across requests.
- `session_id` is only available for HTTP transports (SSE / Streamable HTTP). It is `None` for stdio and in-memory transports.
- Contexts are not thread-safe.

---

## Pattern 1 — In-memory session store (simple)

Use `session_id` as the key for per-session data. Falls back to `request_id` when
`session_id` is unavailable (e.g. stdio transport).

```python
from datetime import datetime
from fastmcp import FastMCP, Context

mcp = FastMCP("SessionServer")
session_store: dict = {}

def _session_key(ctx: Context) -> str:
    return ctx.session_id or ctx.request_id

@mcp.tool
async def store_session_data(data: str, ctx: Context) -> dict:
    key = _session_key(ctx)
    session_store[key] = {"client_id": ctx.client_id, "data": data, "updated": datetime.now()}
    return {"session_key": key}

@mcp.tool
async def get_session_data(ctx: Context) -> dict:
    key = _session_key(ctx)
    return session_store.get(key, {"error": "No data found for current session"})
```

---

## Pattern 2 — Custom session manager

Track multiple sessions per client and expose session metadata as tools:

```python
from typing import Optional
from datetime import datetime
from fastmcp import FastMCP, Context

mcp = FastMCP("ClientTrackingServer")


class SessionManager:
    def __init__(self):
        self.sessions: dict = {}

    def register(self, ctx: Context) -> str:
        key = f"{ctx.client_id or 'unknown'}:{ctx.session_id or ctx.request_id}"
        self.sessions[key] = {
            "client_id": ctx.client_id,
            "session_id": ctx.session_id,
            "request_id": ctx.request_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        return key

    def get(self, key: str) -> Optional[dict]:
        return self.sessions.get(key)

    def find_by_client(self, client_id: str) -> list[dict]:
        return [
            {"key": k, **v}
            for k, v in self.sessions.items()
            if v["client_id"] == client_id
        ]


session_manager = SessionManager()


@mcp.tool
async def register_session(ctx: Context) -> dict:
    key = session_manager.register(ctx)
    return {"session_key": key, "client_id": ctx.client_id}


@mcp.tool
async def get_client_sessions(client_id: str, ctx: Context) -> dict:
    return {
        "client_id": client_id,
        "sessions": session_manager.find_by_client(client_id),
        "current": session_manager.register(ctx),
    }
```

---

## Pattern 3 — Middleware-based auto-tracking

Automatically record every client request without modifying individual tools:

```python
from datetime import datetime
from fastmcp.server.middleware import Middleware, MiddlewareContext

class ClientTrackingMiddleware(Middleware):
    def __init__(self):
        self.active_clients: dict[str, set] = {}
        self.client_requests: dict[str, list] = {}

    async def on_request(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            ctx = context.fastmcp_context
            client_id = ctx.client_id or "anonymous"
            session_id = ctx.session_id or ctx.request_id

            self.active_clients.setdefault(client_id, set()).add(session_id)
            self.client_requests.setdefault(client_id, []).append({
                "method": context.method,
                "session_id": session_id,
                "timestamp": datetime.now(),
            })
        return await call_next(context)


tracking = ClientTrackingMiddleware()
mcp.add_middleware(tracking)


@mcp.tool
async def get_active_clients() -> dict:
    return {
        "clients": {k: list(v) for k, v in tracking.active_clients.items()},
        "total": len(tracking.active_clients),
    }


@mcp.tool
async def get_client_activity(client_id: str) -> dict:
    return {
        "client_id": client_id,
        "sessions": list(tracking.active_clients.get(client_id, [])),
        "recent_requests": tracking.client_requests.get(client_id, [])[-10:],
    }
```

---

## Pattern 4 — External session store (Redis)

For multi-instance deployments where in-memory state is not shared across replicas:

```python
import json
import redis
from fastmcp import FastMCP, Context

mcp = FastMCP("RedisSessionServer")
r = redis.Redis(host="localhost", port=6379, db=0)

@mcp.tool
async def store_context(data: dict, ctx: Context) -> dict:
    session_key = f"session:{ctx.session_id or ctx.request_id}"
    payload = {
        "client_id": ctx.client_id,
        "session_id": ctx.session_id,
        "data": data,
    }
    r.setex(session_key, 3600, json.dumps(payload))  # TTL: 1 hour
    r.sadd(f"client:{ctx.client_id}:sessions", session_key)
    return {"stored": True, "session_key": session_key}

@mcp.tool
async def get_client_sessions(client_id: str) -> dict:
    keys = r.smembers(f"client:{client_id}:sessions")
    sessions = [json.loads(r.get(k)) for k in keys if r.get(k)]
    return {"client_id": client_id, "sessions": sessions, "total": len(sessions)}
```

---

## Choosing a pattern

| Use case | Pattern |
|---|---|
| Single-instance, simple state | In-memory store with `session_id` |
| Per-client tracking, multiple sessions | Custom session manager |
| Automatic instrumentation without modifying tools | Middleware |
| Multi-instance / stateless deployments | Redis or other external store |

---

## References

- [Server Context](https://gofastmcp.com/servers/context)
- [FastMCP Middleware](https://gofastmcp.com/servers/middleware)
