#!/usr/bin/env bash
# =============================================================================
# tests/env/test-mcp-port.sh
# =============================================================================
# Verifies that the MCP_PORT environment variable actually changes the port
# the server binds to. Starts the server twice:
#   1. default (no MCP_PORT) → expects port 8080
#   2. custom  (MCP_PORT=19876) → expects port 19876, NOT 8080
#
# Does NOT require an OPENAPI_TOKEN — only checks TCP connectivity.
#
# Usage:
#   bash tests/env/test-mcp-port.sh
#
# Exit code: 0 if all tests pass, 1 if any fail.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SRC_DIR="$ROOT_DIR/src"

CUSTOM_PORT=19876
DEFAULT_PORT=8080
WAIT_TIMEOUT=20

PASS=0
FAIL=0
SERVER_PID=""

# --- Colors ---
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

pass()    { printf "${GREEN}[PASS]${NC} %s\n" "$1"; PASS=$((PASS+1)); }
fail()    { printf "${RED}[FAIL]${NC} %s\n"   "$1"; FAIL=$((FAIL+1)); }
info()    { printf "${YELLOW}[INFO]${NC} %s\n" "$1"; }
section() { printf "\n${CYAN}=== %s ===${NC}\n" "$1"; }

kill_server() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}

cleanup() {
    kill_server
}
trap cleanup EXIT

# Wait up to $WAIT_TIMEOUT seconds for a TCP port to be reachable.
wait_for_port() {
    local port="$1"
    for i in $(seq 1 "$WAIT_TIMEOUT"); do
        if curl -s --max-time 1 -o /dev/null "http://localhost:${port}/" 2>/dev/null; then
            info "Port ${port} ready after ${i}s"
            return 0
        fi
        sleep 1
    done
    return 1
}

# Check that a port is NOT listening (give it a moment to confirm absence).
port_is_closed() {
    local port="$1"
    ! curl -s --max-time 1 -o /dev/null "http://localhost:${port}/" 2>/dev/null
}

start_server() {
    local port="$1"
    MCP_PORT="$port" PYTHONPATH="$SRC_DIR" \
        python3 -m openapi_mcp_sdk.main \
        > /dev/null 2>&1 &
    SERVER_PID=$!
}

# =============================================================================
# STEP 1 — Custom port (MCP_PORT=19876)
# =============================================================================
section "MCP_PORT=${CUSTOM_PORT} — server binds on custom port"

info "Starting server with MCP_PORT=${CUSTOM_PORT}..."
start_server "$CUSTOM_PORT"

if wait_for_port "$CUSTOM_PORT"; then
    pass "Server is reachable on port ${CUSTOM_PORT}"
else
    fail "Server did not come up on port ${CUSTOM_PORT} within ${WAIT_TIMEOUT}s"
fi

if port_is_closed "$DEFAULT_PORT"; then
    pass "Port ${DEFAULT_PORT} (default) is NOT open — custom port was used"
else
    fail "Port ${DEFAULT_PORT} (default) is also open — MCP_PORT was ignored"
fi

kill_server

# Give the OS a moment to release the ports before the next step.
sleep 2

# =============================================================================
# STEP 2 — Default port (no MCP_PORT set)
# =============================================================================
section "No MCP_PORT — server binds on default port ${DEFAULT_PORT}"

info "Starting server without MCP_PORT..."
start_server "$DEFAULT_PORT"

if wait_for_port "$DEFAULT_PORT"; then
    pass "Server is reachable on default port ${DEFAULT_PORT}"
else
    fail "Server did not come up on default port ${DEFAULT_PORT} within ${WAIT_TIMEOUT}s"
fi

if port_is_closed "$CUSTOM_PORT"; then
    pass "Port ${CUSTOM_PORT} (custom) is NOT open — default port was used"
else
    fail "Port ${CUSTOM_PORT} (custom) is also open — unexpected"
fi

kill_server

# =============================================================================
# Summary
# =============================================================================
printf "\n"
printf "Results: ${GREEN}%d passed${NC}, ${RED}%d failed${NC}\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
