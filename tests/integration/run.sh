#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CASES_DIR="$SCRIPT_DIR/cases"
MCP_CONFIG="$ROOT_DIR/.mcp.json"

PASS=0
FAIL=0
SERVER_PID=""

cleanup() {
    rm -f "$MCP_CONFIG"
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

# --- pre-flight checks ---

if [ -z "${OPENAPI_TOKEN:-}" ]; then
    echo "ERROR: OPENAPI_TOKEN is not set."
    echo "       Export it before running: export OPENAPI_TOKEN=your_token"
    exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
    echo "ERROR: 'claude' CLI not found."
    echo "       Install Claude Code: https://claude.ai/code"
    exit 1
fi

# --- write temporary MCP config ---

cat > "$MCP_CONFIG" <<EOF
{
  "mcpServers": {
    "openapi": {
      "type": "http",
      "url": "http://localhost:8080/mcp/",
      "headers": {
        "Authorization": "Bearer ${OPENAPI_TOKEN}"
      }
    }
  }
}
EOF

# --- start server in background ---

echo "Starting MCP server..."
cd "$ROOT_DIR"
PYTHONPATH=src uv run uvicorn openapi_mcp_server.main:app \
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

    response=$(cd "$ROOT_DIR" && claude --print "$prompt" 2>&1)

    failed=0
    while IFS= read -r pattern; do
        # skip blank lines and comments
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