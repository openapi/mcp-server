#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_CONFIG="$ROOT_DIR/.mcp.json"

SERVER_PID=""

# Sandbox mode: SANDBOX=1 uses OPENAPI_SANDBOX_TOKEN and test.* endpoints
SANDBOX="${SANDBOX:-0}"
if [ "$SANDBOX" = "1" ]; then
    TOKEN="${OPENAPI_SANDBOX_TOKEN:-}"
    K_SERVICE_VALUE="test-openapi-mcp-server"
    MODE_LABEL="SANDBOX"
else
    TOKEN="${OPENAPI_TOKEN:-}"
    K_SERVICE_VALUE=""
    MODE_LABEL="PRODUCTION"
fi

cleanup() {
    rm -f "$MCP_CONFIG"
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
    echo ""
    echo "MCP server stopped. Session ended."
}
trap cleanup EXIT

# --- pre-flight checks ---

if [ -z "$TOKEN" ]; then
    if [ "$SANDBOX" = "1" ]; then
        echo "ERROR: OPENAPI_SANDBOX_TOKEN is not set."
        echo "       export OPENAPI_SANDBOX_TOKEN=your_sandbox_token"
    else
        echo "ERROR: OPENAPI_TOKEN is not set."
        echo "       export OPENAPI_TOKEN=your_token"
        echo "       For sandbox mode: SANDBOX=1 make try-claude"
    fi
    exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
    echo "ERROR: 'claude' CLI not found."
    echo "       Install Claude Code: https://claude.ai/code"
    exit 1
fi

echo "Mode: $MODE_LABEL"

# --- write temporary MCP config ---

cat > "$MCP_CONFIG" <<EOF
{
  "mcpServers": {
    "openapi": {
      "type": "http",
      "url": "http://localhost:8080/mcp/",
      "headers": {
        "Authorization": "Bearer ${TOKEN}"
      }
    }
  }
}
EOF

# --- start server in background ---

echo "Starting MCP server..."
cd "$ROOT_DIR"
K_SERVICE="$K_SERVICE_VALUE" PYTHONPATH=src uv run uvicorn openapi_mcp_server.main:app \
    --host 0.0.0.0 --port 8080 --log-level warning &
SERVER_PID=$!

echo "Waiting for server on :8080..."
for i in $(seq 1 30); do
    if curl -s --max-time 1 http://localhost:8080/ -o /dev/null 2>&1; then
        echo "Server ready."
        break
    fi
    sleep 1
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Server did not start within 30 seconds."
        exit 1
    fi
done

echo ""
echo "MCP tools active — openapi.com APIs are available in this session."
echo "Press Ctrl+C or type /exit to stop."
echo ""

# --- open Claude interactively with MCP already configured ---

unset CLAUDECODE 2>/dev/null || true
claude
