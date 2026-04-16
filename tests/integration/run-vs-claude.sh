#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CASES_DIR="$SCRIPT_DIR/cases"
MCP_CONFIG="$ROOT_DIR/.mcp.json"

PASS=0
FAIL=0
SERVER_PID=""

# Sandbox mode: SANDBOX=1 uses OPENAPI_SANDBOX_TOKEN and test.* endpoints
SANDBOX="${SANDBOX:-0}"
if [ "$SANDBOX" = "1" ]; then
    TOKEN="${OPENAPI_SANDBOX_TOKEN:-}"
    MCP_OPENAPI_ENV_VALUE="test"
else
    TOKEN="${OPENAPI_TOKEN:-}"
    MCP_OPENAPI_ENV_VALUE=""
fi

cleanup() {
    rm -f "$MCP_CONFIG"
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
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
        echo "       For sandbox mode: SANDBOX=1 export OPENAPI_SANDBOX_TOKEN=your_token"
    fi
    exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
    echo "ERROR: 'claude' CLI not found."
    echo "       Install Claude Code: https://claude.ai/code"
    exit 1
fi

[ "$SANDBOX" = "1" ] && echo "Mode: SANDBOX" || echo "Mode: PRODUCTION"

# --- write temporary MCP config ---

cat > "$MCP_CONFIG" <<EOF
{
  "mcpServers": {
    "openapi-local": {
      "type": "http",
      "url": "http://localhost:8080",
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
MCP_OPENAPI_ENV="$MCP_OPENAPI_ENV_VALUE" PYTHONPATH=src uv run uvicorn openapi_mcp_sdk.main:app \
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

# --- run each test case ---

for case_dir in "$CASES_DIR"/*/; do
    name=$(basename "$case_dir")
    prompt=$(cat "$case_dir/prompt.txt")

    response=$(cd "$ROOT_DIR" && unset CLAUDECODE && claude --print --dangerously-skip-permissions "$prompt" 2>&1)

    failed=0
    while IFS= read -r pattern; do
        [[ -z "$pattern" || "$pattern" == \#* ]] && continue
        if ! echo "$response" | grep -qi "$pattern"; then
            echo "[FAIL] $name — expected pattern not found: '$pattern'"
            failed=1
        fi
    done < "$case_dir/expect.txt"

    if [ "$failed" -eq 0 ]; then
        echo "[PASS] $name"
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
        echo "       Response preview:"
        echo "$response" | head -8 | sed 's/^/         /'
    fi
done

# --- summary ---

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
