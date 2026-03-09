#!/usr/bin/env bash
# Start the MCP server and expose it publicly via ngrok (if installed).
# Usage: bash scripts/start.sh
# Env:   PORT (default 8080), HOST (default 0.0.0.0)
#        NGROK_DOMAIN — set to your reserved ngrok static domain to get a
#                       stable URL that never changes across restarts.
#                       Claim your free static domain at:
#                       https://dashboard.ngrok.com/domains
#        Example:
#                       export NGROK_DOMAIN=your-name.ngrok-free.app

set -uo pipefail

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
NGROK_DOMAIN="${NGROK_DOMAIN:-}"

SERVER_PID=""
NGROK_PID=""

cleanup() {
    [ -n "$NGROK_PID" ] && kill "$NGROK_PID" 2>/dev/null || true
    [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── clear Python bytecode cache so edited sources are always reloaded ──────
find src/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ── start uvicorn ──────────────────────────────────────────────────────────
PYTHONPATH=src uv run uvicorn openapi_mcp_sdk.main:app --host "$HOST" --port "$PORT" &
SERVER_PID=$!

# ── wait for server to accept connections ──────────────────────────────────
printf "Waiting for server\n"
for i in $(seq 1 30); do
    if curl -s --max-time 1 "http://localhost:$PORT/" > /dev/null 2>&1; then
        break
    fi
    sleep 1
done
echo ""

# ── ngrok ──────────────────────────────────────────────────────────────────
if ! command -v ngrok > /dev/null 2>&1; then
    echo "  (ngrok not found — skipping public URL)"
    echo "  Install from https://ngrok.com/download to get a public URL."
    wait "$SERVER_PID" 2>/dev/null || true
    exit 0
fi

if [ -n "$NGROK_DOMAIN" ]; then
    ngrok http "$PORT" --domain="$NGROK_DOMAIN" --log=stdout > /tmp/ngrok-mcp.log 2>&1 &
else
    ngrok http "$PORT" --log=stdout > /tmp/ngrok-mcp.log 2>&1 &
fi
NGROK_PID=$!

# poll the ngrok local API until the tunnel URL is available or ngrok exits with an error
NGROK_URL=""
for i in $(seq 1 20); do
    # check if ngrok process died early (auth error, config error, etc.)
    if ! kill -0 "$NGROK_PID" 2>/dev/null; then
        NGROK_ERROR=$(grep -oP 'ERROR:\s+\K.+' /tmp/ngrok-mcp.log | grep -v '^\s*$' | head -5)
        echo "  ngrok failed to start:"
        while IFS= read -r line; do
            echo "    $line"
        done <<< "$NGROK_ERROR"
        NGROK_PID=""
        wait "$SERVER_PID" 2>/dev/null || true
        exit 0
    fi
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    tunnels = json.load(sys.stdin).get('tunnels', [])
    https = [t['public_url'] for t in tunnels if t['public_url'].startswith('https')]
    print(https[0] if https else '')
except Exception:
    pass
" 2>/dev/null)
    [ -n "$NGROK_URL" ] && break
    sleep 1
done

SEP="========================================================="
if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "$SEP"
    echo "ngrok   ${NGROK_URL}"
    echo "local   http://localhost:${PORT}"
    echo "$SEP"
    echo ""
else
    echo "ngrok started but tunnel URL not available."
    echo "Check the dashboard at http://localhost:4040"
fi

wait "$SERVER_PID" 2>/dev/null || true
