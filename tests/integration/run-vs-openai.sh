#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CASES_DIR="$SCRIPT_DIR/cases"

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

# MCP_URL: the URL OpenAI will use to reach the MCP server.
# OpenAI cloud CANNOT reach localhost — expose the server first:
#   ngrok http 8080
#   MCP_URL=https://xxxx.ngrok-free.app make test-openai
MCP_URL="${MCP_URL:-http://localhost:8080}"

cleanup() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# --- pre-flight checks ---

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY is not set."
    echo "       export OPENAI_API_KEY=sk-..."
    exit 1
fi

if [ -z "$TOKEN" ]; then
    if [ "$SANDBOX" = "1" ]; then
        echo "ERROR: OPENAPI_SANDBOX_TOKEN is not set."
        echo "       export OPENAPI_SANDBOX_TOKEN=your_sandbox_token"
    else
        echo "ERROR: OPENAPI_TOKEN is not set."
        echo "       export OPENAPI_TOKEN=your_token"
    fi
    exit 1
fi

if echo "$MCP_URL" | grep -qE "localhost|127\.0\.0\.1"; then
    echo "WARNING: MCP_URL='$MCP_URL' — OpenAI cloud cannot reach localhost."
    echo "         Expose the server with ngrok and set MCP_URL to the public URL:"
    echo "           ngrok http 8080"
    echo "           MCP_URL=https://xxxx.ngrok-free.app make test-openai"
    echo ""
fi

[ "$SANDBOX" = "1" ] && echo "Mode: SANDBOX" || echo "Mode: PRODUCTION"
echo "MCP_URL: $MCP_URL"

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

# --- ask OpenAI via Responses API (with or without MCP tools) ---

ask_openai() {
    local prompt="$1"
    local use_mcp="$2"
    local payload

    if [ "$use_mcp" = "1" ]; then
        payload=$(jq -n \
            --arg prompt "$prompt" \
            --arg mcp_url "$MCP_URL" \
            --arg token "$TOKEN" \
            '{
                model: "gpt-4o-mini",
                input: $prompt,
                tools: [{
                    type: "mcp",
                    server_label: "openapi",
                    server_url: $mcp_url,
                    require_approval: "never",
                    headers: { Authorization: ("Bearer " + $token) }
                }]
            }')
    else
        payload=$(jq -n --arg prompt "$prompt" '{model: "gpt-4o-mini", input: $prompt}')
    fi

    curl -sf https://api.openai.com/v1/responses \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        | jq -r '[.output[] | select(.type == "message") | .content[] | select(.type == "output_text") | .text] | join("\n")'
}

# --- run each test case ---

for case_dir in "$CASES_DIR"/*/; do
    name=$(basename "$case_dir")
    prompt=$(cat "$case_dir/prompt.txt")

    # Cases with a 'no-mcp' marker are run without MCP tools
    # (useful for sanity checks or cases that don't need the server)
    use_mcp=1
    [ -f "$case_dir/no-mcp" ] && use_mcp=0

    if [ "$use_mcp" = "1" ] && echo "$MCP_URL" | grep -qE "localhost|127\.0\.0\.1"; then
        echo "[SKIP] $name — MCP_URL is localhost, OpenAI cannot reach it"
        continue
    fi

    response=$(ask_openai "$prompt" "$use_mcp")

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
