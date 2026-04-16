#!/usr/bin/env bash
# Start the MCP server and expose it publicly via ngrok (if installed).
# Usage: bash scripts/start.sh
# Env:   MCP_PORT (default 8080), HOST (default 0.0.0.0)
#        MCP_ENV (default dev), DEV_MODE (default 1)
#        NGROK_DOMAIN — set to your reserved ngrok static domain to get a
#                       stable URL that never changes across restarts.
#                       Claim your free static domain at:
#                       https://dashboard.ngrok.com/domains
#        Example:
#                       export NGROK_DOMAIN=your-name.ngrok-free.app

set -uo pipefail

MCP_PORT="${MCP_PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
MCP_ENV="${MCP_ENV:-dev}"
DEV_MODE="${DEV_MODE:-1}"
NGROK_DOMAIN="${NGROK_DOMAIN:-}"

SERVER_PID=""
NGROK_PID=""

cleanup() {
    if [ -n "$NGROK_PID" ]; then
        kill "$NGROK_PID" 2>/dev/null || true
    fi
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

clear_python_cache() {
    find src/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
}

start_server() {
    clear_python_cache
    PYTHONPATH=src MCP_ENV="$MCP_ENV" \
        uv run uvicorn openapi_mcp_sdk.main:app \
        --host "$HOST" \
        --port "$MCP_PORT" \
        --log-config scripts/log_config.json &
    SERVER_PID=$!
}

stop_server() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    wait "$SERVER_PID" 2>/dev/null || true
    SERVER_PID=""
}

snapshot_sources() {
    find src tests scripts -type f \( -name '*.py' -o -name '*.php' \) -print0 2>/dev/null \
        | sort -z \
        | xargs -0 stat -c '%n:%Y' 2>/dev/null
}

# ── start uvicorn ──────────────────────────────────────────────────────────
start_server

# ── wait for server to accept connections ──────────────────────────────────
printf "Waiting for server\n"
for _ in $(seq 1 30); do
    if curl -s --max-time 1 "http://localhost:$MCP_PORT/" > /dev/null 2>&1; then
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
    ngrok http "$MCP_PORT" --domain="$NGROK_DOMAIN" --log=stdout > /tmp/ngrok-mcp.log 2>&1 &
else
    ngrok http "$MCP_PORT" --log=stdout > /tmp/ngrok-mcp.log 2>&1 &
fi
NGROK_PID=$!

# poll the ngrok local API until the tunnel URL is available or ngrok exits with an error
NGROK_URL=""
for _ in $(seq 1 20); do
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
    echo "local   http://localhost:${MCP_PORT}"
    echo "$SEP"
    echo ""
else
    echo "ngrok started but tunnel URL not available."
    echo "Check the dashboard at http://localhost:4040"
fi

if [ "$DEV_MODE" != "1" ]; then
    wait "$SERVER_PID" 2>/dev/null || true
    exit 0
fi

echo "dev mode enabled (MCP_ENV=${MCP_ENV})"
echo "watching *.py and *.php for changes"

LAST_SNAPSHOT="$(snapshot_sources)"
while true; do
    sleep 1

    if [ -n "$SERVER_PID" ] && ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "server exited, restarting..."
        start_server
        LAST_SNAPSHOT="$(snapshot_sources)"
        continue
    fi

    CURRENT_SNAPSHOT="$(snapshot_sources)"
    if [ "$CURRENT_SNAPSHOT" != "$LAST_SNAPSHOT" ]; then
        echo "source change detected, restarting server..."
        stop_server
        start_server
        LAST_SNAPSHOT="$CURRENT_SNAPSHOT"
    fi
done
