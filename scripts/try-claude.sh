#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Isolated workspace: Claude starts in an empty temp dir so it doesn't
# pick up files or context from the project codebase.
WORK_DIR="$(mktemp -d /tmp/openapi-try-XXXXXX)"

SERVER_PID=""
MCP_REGISTERED=0
MCP_SERVER_NAME="openapi-local"

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
    if [ "$MCP_REGISTERED" = "1" ]; then
        claude mcp remove --scope user "$MCP_SERVER_NAME" 2>/dev/null || true
        echo "MCP server '$MCP_SERVER_NAME' removed from user settings."
    fi
    rm -rf "$WORK_DIR"
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
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

if ! command -v openapi >/dev/null 2>&1; then
    echo "ERROR: 'openapi' CLI not found."
    echo "       Install it: cargo install openapi-cli-rs"
    exit 1
fi

echo "Mode: $MODE_LABEL"

# --- validate token against the live API ---

echo "Validating token..."
if [ "$SANDBOX" = "1" ]; then
    VALIDATION_OUTPUT=$(OPENAPI_SANDBOX_TOKEN="$TOKEN" openapi -S exchange-rate get 2>&1) || {
        echo "ERROR: Token validation failed (sandbox)."
        echo "       $VALIDATION_OUTPUT"
        echo "       Check that OPENAPI_SANDBOX_TOKEN is correct."
        exit 1
    }
else
    VALIDATION_OUTPUT=$(OPENAPI_TOKEN="$TOKEN" openapi exchange-rate get 2>&1) || {
        echo "ERROR: Token validation failed (production)."
        echo "       $VALIDATION_OUTPUT"
        echo "       Check that OPENAPI_TOKEN is correct."
        exit 1
    }
fi
echo "Token valid."

# --- start server in background ---

echo "Starting MCP server..."
cd "$ROOT_DIR"

# Clear Python bytecode cache so any newly added modules are always
# loaded fresh rather than served from stale .pyc files.
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

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

# --- register MCP server in user-level Claude settings ---
# Using --scope user writes to ~/.claude/settings.json so Claude picks it
# up regardless of which directory it starts in. Removed on EXIT.

echo "Registering MCP server in user settings..."
# Remove stale entry from a previous crashed session, if any.
claude mcp remove --scope user "$MCP_SERVER_NAME" 2>/dev/null || true
claude mcp add \
    --transport http \
    --scope user \
    "$MCP_SERVER_NAME" \
    "http://localhost:8080/mcp/" \
    --header "Authorization: Bearer ${TOKEN}"
MCP_REGISTERED=1
echo "Registered: $MCP_SERVER_NAME → http://localhost:8080/mcp/"

echo ""
echo "MCP tools active — openapi.com APIs are available in this session."
echo "Working directory: $WORK_DIR"
echo "Press Ctrl+C or type /exit to stop."
echo ""

# --- open Claude interactively from the isolated temp workspace ---
# cd into the empty temp dir so Claude has no access to the project codebase.

unset CLAUDECODE 2>/dev/null || true
cd "$WORK_DIR"
claude
