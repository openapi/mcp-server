## Quick context for AI coding agents

This repository implements the Openapi.com MCP gateway (FastAPI + FastMCP). The server acts as a proxy that forwards a client's Bearer token to downstream Openapi services and exposes MCP tools implemented under `src/openapi_mcp_sdk/apis/`.

Key files
- `src/openapi_mcp_sdk/main.py` — application entry point. Mounts the MCP app and contains HTTP endpoints `/callbacks` and `/status/{request_id}`. Shows how token query params are converted into an Authorization header.
- `src/openapi_mcp_sdk/mcp_core.py` — central FastMCP instance (`mcp`), helper `make_api_call(ctx, method, url, ...)`, and `processPolling` for handling async callbacks.
- `src/openapi_mcp_sdk/memory_store.py` — in-memory + Memcached-backed callback result store. Exposes `get_callback_result` and `set_callback_result` and defines `BASE_URL`, `callbackUrl` and memcached config from env vars.
- `src/openapi_mcp_sdk/apis/` — each module defines one or more tools decorated with `@mcp.tool`. Importing these modules triggers tool registration.

What matters for code changes
- Tools are registered when the `apis` modules are imported by `main.py`. Don't remove those imports unless you know how to re-register tools.
- `make_api_call` relies on extracting the Authorization header from FastMCP internals or `ctx.request_context.request.headers`. Many tools assume the client supplied `Authorization: Bearer <token>` (or `?token=` query param).
- Async APIs use a callback workflow: downstream APIs accept a `callback` object with `url` and `custom` (see `company.py`). Callbacks are saved with `set_callback_result` and read with `get_callback_result`.

Common patterns and code examples
- Registering a tool (example from `company.py`):
  - Add `@mcp.tool` above an async function with `ctx: Context` as last arg.
  - Use `make_api_call(ctx, "GET", url)` to proxy authenticated requests.
- Creating an async callback request (company full profile):
  - Build `custom_context = {"request_id": getSessionHash(ctx), ...}`
  - POST to the downstream `.../callback` endpoint with `callback.url = memory store callbackUrl` and `callback.custom = custom_context`.
  - Use `processPolling(ctx, request_id, ...)` to wait/poll stored results.

Environment and runtime
- Run locally: `python src/openapi_mcp_sdk/main.py` (README shows `python main.py` from project root; in this layout use the module path). The server binds to 0.0.0.0:PORT (reads `PORT` env var, default 80).
- Virtualenv: repository uses `uv` in README but `pyproject.toml` shows `requires-python = ">=3.13"`. Note: README states Python 3.9+. If you modify runtime or CI, confirm the correct Python target.
- Memcached configuration is read from `MEMCACHED_HOST`, `MEMCACHED_PORT`, and `X-DEV-VM`/`K_SERVICE` influence defaults. Tests or dev runs can run with a mocked `memory_store` (it falls back to in-process dict on Memcached errors).

Developer workflows (concrete)
- Start server (local):
  - Create venv and install requirements (README): `uv venv && source .venv/bin/activate && uv pip install -r requirements.txt`
  - Run: `python src/openapi_mcp_sdk/main.py` (or use `uvicorn` as in `if __name__ == '__main__'`).
- Docker: see `Dockerfile` and README.
- Debugging tips:
  - Check printed logs: `main.py` and `mcp_core.make_api_call` print request details and errors.
  - Use `/status/{request_id}` to inspect async request state set by callbacks.
  - If memcached calls fail, memory fallbacks provide predictable behavior.

Conventions and gotchas for agents
- Do not add or hardcode secrets (tokens/keys) into code — this project explicitly expects the client to supply Bearer tokens. Keep token handling in middleware or test fixtures.
- When adding a new API/tool module:
  - Follow the `@mcp.tool` decorator pattern and ensure the module is imported from `main.py` or otherwise registered during startup.
  - Prefer to call `make_api_call` for HTTP interactions so the common auth/header extraction is reused.
- Beware `BASE_URL` / `callbackUrl` derivation in `memory_store.py` — it depends on `K_SERVICE` and `X-DEV-VM`. Tests running on CI may need to set these env vars.
- The code expects `ctx` to contain `request_context.request.headers` in some places; use defensive checks when reading headers if you add new code paths.

What I couldn't verify automatically
- Exact developer commands for `uv` usage and environment variants are described in README; confirm whether you prefer `python -m venv` flows or `uv` for reproducibility. Also confirm the Python version (pyproject vs README).

If anything here is unclear or you want additional examples (e.g., a sample new tool, unit test scaffolding, CI snippets), tell me which sections to expand and I will iterate.
