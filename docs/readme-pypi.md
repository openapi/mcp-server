# openapi-mcp-sdk

The official [openapi.com](https://openapi.com/) MCP SDK.

Use it in two ways:

- **Ready-to-use server** — start a fully configured MCP gateway from the command line
  with a single command, no setup required.
- **Python library** — import `openapi_mcp_sdk` in your own project to build a
  custom MCP server on top of openapi.com APIs.

---

## Run the server

### One-liner (no install required)

```bash
uvx openapi-mcp-sdk server
```

The server starts at `http://localhost:8080`.

### Other runtimes

```bash
# pipx — ephemeral run, no install needed
pipx run openapi-mcp-sdk server

# pip — install once, run anytime
pip install openapi-mcp-sdk && openapi-mcp-sdk server
```

---

## Local launcher script

Copy and paste the block below into your terminal. It creates a ready-to-use
`mcp-server.sh` file and immediately starts the server:

```bash
cat > mcp-server.sh << 'EOF'
#!/bin/bash
# ============================================================
# Openapi.com MCP Server — local launcher
# Edit the variables below, then run: bash mcp-server.sh
# ============================================================

export PORT="${PORT:-8080}"
export SERVICES_CREDENTIALS="${SERVICES_CREDENTIALS:-{}}"

uvx openapi-mcp-sdk server
EOF
bash mcp-server.sh
```

Next time, just run:

```bash
bash mcp-server.sh
```

---

## CLI reference

```
openapi-mcp-sdk <command>

Commands:
  server   Start the MCP server (HTTP/SSE, default port 8080)
  ping     Ping the openapi.com APIs and report latency       [coming soon]
  token    Generate or inspect an openapi.com Bearer token    [coming soon]
```

---

## MCP client configuration

Point any MCP-compatible client (VS Code, Claude Desktop, …) at the running server.

Get your Bearer Token at [console.openapi.com](https://console.openapi.com/oauth).

**With Authorization header (recommended):**

```json
{
  "servers": {
    "openapi.com": {
      "type": "http",
      "url": "http://localhost:8080/",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

**With `?token=` query parameter** (for clients that do not support custom headers):

```json
{
  "servers": {
    "openapi.com": {
      "type": "http",
      "url": "http://localhost:8080/?token=YOUR_TOKEN"
    }
  }
}
```

The server automatically promotes `?token=` to an `Authorization: Bearer` header,
so both methods behave identically.

---

## Links

- [Full documentation & source](https://github.com/openapi/mcp-server)
- [openapi.com](https://openapi.com/)
- [MCP specification](https://github.com/modelcontextprotocol/specification)
