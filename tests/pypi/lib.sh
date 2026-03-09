#!/bin/bash
# =============================================================================
# tests/pypi/lib.sh — shared helpers for PyPI package tests
# =============================================================================
# Source this file: source "$(dirname "$0")/lib.sh"
# =============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WHEEL="$(ls "$REPO_ROOT"/dist/openapi_mcp_sdk-*.whl 2>/dev/null | sort -V | tail -1)"
TARBALL="$(ls "$REPO_ROOT"/dist/openapi_mcp_sdk-*.tar.gz 2>/dev/null | sort -V | tail -1)"

# --- colours ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RESET='\033[0m'

pass() { echo -e "${GREEN}  PASS${RESET}  $*"; }
fail() { echo -e "${RED}  FAIL${RESET}  $*"; }
info() { echo -e "${YELLOW}  INFO${RESET}  $*"; }

# require_wheel — abort if no wheel found
require_wheel() {
    if [[ -z "$WHEEL" ]]; then
        fail "No wheel found in dist/. Run: uv build"
        exit 1
    fi
    info "Using wheel: $(basename "$WHEEL")"
}

# require_cmd <cmd> — skip test if command not available
require_cmd() {
    if ! command -v "$1" &>/dev/null; then
        info "Skipping — '$1' not found in PATH"
        exit 0
    fi
}

# start_server <port> <launch-command...>
#   Starts the server in background on the given port.
#   Sets global SERVER_PID.
start_server() {
    local port="$1"; shift
    export PORT="$port"
    "$@" >/tmp/pypi-test-server-$port.log 2>&1 &
    SERVER_PID=$!
}

# wait_for_server <pid> <port> [timeout_seconds=60]
#   Polls http://localhost:<port>/status/probe until it responds (any HTTP code).
#   Also aborts early if the process <pid> has already exited.
#   Returns 0 on success, 1 on timeout or early exit.
wait_for_server() {
    local pid="$1"
    local port="$2"
    local timeout="${3:-60}"
    local elapsed=0
    while (( elapsed < timeout )); do
        # abort early if the server process died
        if ! kill -0 "$pid" 2>/dev/null; then
            return 1
        fi
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 \
               "http://localhost:$port/status/probe" 2>/dev/null)
        if [[ -n "$code" && "$code" != "000" ]]; then
            return 0
        fi
        sleep 1
        (( elapsed++ ))
    done
    return 1
}

# stop_server
stop_server() {
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null
        wait "$SERVER_PID" 2>/dev/null
    fi
    SERVER_PID=
}

# run_test <port> <description> <launch-command...>
#   Full test cycle: start → wait → probe → stop → report.
#   Returns 0 (pass) or 1 (fail).
run_test() {
    local port="$1";       shift
    local description="$1"; shift

    info "Testing: $description (port $port)"
    start_server "$port" "$@"

    if wait_for_server "$SERVER_PID" "$port" 60; then
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 \
                    "http://localhost:$port/status/probe" 2>/dev/null)
        stop_server
        pass "$description → HTTP $http_code"
        return 0
    else
        stop_server
        if ! kill -0 "${SERVER_PID:-0}" 2>/dev/null; then
            fail "$description → server exited before responding"
        else
            fail "$description → server did not respond within timeout"
        fi
        if [[ -f "/tmp/pypi-test-server-$port.log" ]]; then
            echo "--- server log ---"
            tail -20 "/tmp/pypi-test-server-$port.log"
            echo "------------------"
        fi
        return 1
    fi
}
