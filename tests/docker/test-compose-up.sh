#!/usr/bin/env bash
# =============================================================================
# tests/docker/test-compose-up.sh
# =============================================================================
# Smoke tests for the MCP server running via docker compose (latest image).
# Exercises the MCP JSON-RPC 2.0 protocol over HTTP (streamable transport)
# and the non-MCP REST endpoints exposed by FastAPI.
#
# Does NOT require a real openapi.com Bearer token — only openapi_server_info
# is called, which reads internal state with no external API calls.
#
# Usage:
#   bash tests/docker/test-compose-up.sh
#   MCP_URL=http://myserver:8080 bash tests/docker/test-compose-up.sh
#
# Exit code: 0 if all tests pass, 1 if any fail.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVER_URL="${MCP_URL:-http://localhost:8080}"
PASS=0
FAIL=0
CONTAINER_STARTED=0
_TMPDIR=$(mktemp -d)

# --- Colors ---
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# --- Output helpers ---
pass()    { printf "${GREEN}[PASS]${NC} %s\n"    "$1"; PASS=$((PASS+1)); }
fail()    { printf "${RED}[FAIL]${NC} %s\n"      "$1"; FAIL=$((FAIL+1)); }
info()    { printf "${YELLOW}[INFO]${NC} %s\n"   "$1"; }
section() { printf "\n${CYAN}=== %s ===${NC}\n"  "$1"; }

# Cleanup: remove temp files and stop the container if we started it
cleanup() {
    rm -rf "$_TMPDIR"
    if [ "$CONTAINER_STARTED" -eq 1 ]; then
        info "Stopping container..."
        (
            cd "$ROOT_DIR" &&
            docker compose -f compose.yml down --remove-orphans 2>/dev/null
        ) || true
    fi
}
trap cleanup EXIT

# Assert a pattern is present in a response body
assert_contains() {
    local label="$1" body="$2" pattern="$3"
    if echo "$body" | grep -q "$pattern"; then
        pass "$label"
    else
        fail "$label — expected '$pattern' not found"
        printf "  Response (first 300 chars): %s\n" "$(echo "$body" | head -c 300)"
    fi
}

# Assert two values are equal
assert_eq() {
    local label="$1" actual="$2" expected="$3"
    if [ "$actual" = "$expected" ]; then
        pass "$label (= $expected)"
    else
        fail "$label — expected '$expected', got '$actual'"
    fi
}

# Parse a curl response: handle both plain JSON and SSE (data: ...) format.
# Returns the JSON-RPC body of the last result/error message.
parse_mcp_response() {
    local raw="$1"
    if echo "$raw" | grep -q '^data:'; then
        # SSE stream — find the last "data:" line containing a jsonrpc result or error
        local line
        line=$(echo "$raw" | grep '^data:' | grep -E '"result"|"error"' | tail -1 | sed 's/^data: //')
        if [ -n "$line" ]; then
            echo "$line"
        else
            echo "$raw" | grep '^data:' | tail -1 | sed 's/^data: //'
        fi
    else
        echo "$raw"
    fi
}

# POST a JSON-RPC payload to the MCP endpoint.
# $1 = JSON payload
# $2 = session ID (optional)
# Writes response headers to $_TMPDIR/last_headers.txt
# --max-time 15: prevents curl from hanging on an open SSE stream.
mcp_post() {
    local payload="$1"
    local session="${2:-}"
    local hfile="$_TMPDIR/last_headers.txt"
    local args=(
        -s
        --max-time 15
        -D "$hfile"
        -X POST "$SERVER_URL/"
        -H "Content-Type: application/json"
        -H "Accept: application/json, text/event-stream"
        -H "Authorization: Bearer test-smoke-token"
    )
    [ -n "$session" ] && args+=(-H "Mcp-Session-Id: $session")
    curl "${args[@]}" -d "$payload"
}

# Extract the Mcp-Session-Id header value from the last mcp_post headers file
extract_session_id() {
    awk -F': ' 'tolower($1) == "mcp-session-id" { gsub(/\r/, ""); print $2; exit }' \
        "$_TMPDIR/last_headers.txt" 2>/dev/null || true
}

# =============================================================================
# STEP 1 — Start the container (latest image, no debug overlay)
# =============================================================================
section "Docker Compose"

cd "$ROOT_DIR"
info "Building and starting the MCP container (latest image)..."
docker compose -f compose.yml up --build -d
CONTAINER_STARTED=1

info "Waiting for server at $SERVER_URL (up to 90s)..."
for i in $(seq 1 90); do
    if curl -s --max-time 2 -o /dev/null "$SERVER_URL/" 2>/dev/null; then
        info "Server ready after ${i}s"; break
    fi
    sleep 1
    if [ "$i" -eq 90 ]; then
        fail "Server did not respond within 90s"
        docker compose -f compose.yml logs mcp | tail -30
        exit 1
    fi
done

# =============================================================================
# STEP 2 — MCP initialize (protocol handshake)
# =============================================================================
section "MCP — initialize"

INIT_RAW=$(mcp_post '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl-smoke-test","version":"1.0"}}}')
INIT_BODY=$(parse_mcp_response "$INIT_RAW")

assert_contains "initialize → jsonrpc result"   "$INIT_BODY" '"result"'
assert_contains "initialize → protocolVersion"  "$INIT_BODY" '"protocolVersion"'
assert_contains "initialize → serverInfo"       "$INIT_BODY" '"serverInfo"'
assert_contains "initialize → capabilities"     "$INIT_BODY" '"capabilities"'
assert_contains "initialize → server name"      "$INIT_BODY" 'Openapi'

SESSION_ID=$(extract_session_id)
if [ -n "$SESSION_ID" ]; then
    pass "initialize → Mcp-Session-Id received"
    info "Session: $SESSION_ID"
else
    info "No Mcp-Session-Id in response headers (stateless mode)"
fi

# Send notifications/initialized to complete the handshake
mcp_post '{"jsonrpc":"2.0","method":"notifications/initialized"}' "$SESSION_ID" \
    -o /dev/null 2>/dev/null || true

# =============================================================================
# STEP 3 — MCP tools/list
# =============================================================================
section "MCP — tools/list"

LIST_RAW=$(mcp_post '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' "$SESSION_ID")
LIST_BODY=$(parse_mcp_response "$LIST_RAW")

assert_contains "tools/list → jsonrpc result"           "$LIST_BODY" '"result"'
assert_contains "tools/list → tools array"              "$LIST_BODY" '"tools"'
assert_contains "tools/list → openapi_server_info"      "$LIST_BODY" '"openapi_server_info"'

TOOL_COUNT=$(python3 -c \
    "import sys, json; d=json.loads(sys.stdin.read()); print(len(d.get('result',{}).get('tools',[])))" \
    <<< "$LIST_BODY" 2>/dev/null || echo "0")
if [ "$TOOL_COUNT" -gt 0 ] 2>/dev/null; then
    pass "tools/list → $TOOL_COUNT tools registered"
else
    fail "tools/list → could not count tools (got: '$TOOL_COUNT')"
fi

# =============================================================================
# STEP 4 — MCP tools/call: openapi_server_info (no external API call)
# =============================================================================
section "MCP — tools/call openapi_server_info"

CALL_RAW=$(mcp_post \
    '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"openapi_server_info","arguments":{}}}' \
    "$SESSION_ID")
CALL_BODY=$(parse_mcp_response "$CALL_RAW")

assert_contains "tools/call → jsonrpc result"           "$CALL_BODY" '"result"'
assert_contains "tools/call → content array"            "$CALL_BODY" '"content"'
assert_contains "tools/call → isError false"            "$CALL_BODY" 'false'
assert_contains "tools/call → server name in payload"   "$CALL_BODY" 'Openapi'
assert_contains "tools/call → status ok in payload"     "$CALL_BODY" 'status'

# =============================================================================
# STEP 5 — REST endpoints (FastAPI, outside MCP)
# =============================================================================
section "REST Endpoints"

# POST /callbacks with a missing required field → error JSON
CB_BODY=$(curl -s --max-time 10 -X POST "$SERVER_URL/callbacks" \
    -H "Content-Type: application/json" \
    -d '{"unexpected_field": true}')
assert_contains "POST /callbacks (bad body) → error field" "$CB_BODY" '"error"'

# GET /status/<unknown-id> → 404
STATUS_CODE=$(curl -s --max-time 10 -o /dev/null -w "%{http_code}" \
    "$SERVER_URL/status/nonexistent-smoke-test-id-$(date +%s)")
assert_eq "GET /status/<unknown> → 404" "$STATUS_CODE" "404"

# GET /.well-known/oauth-authorization-server → JSON error (not plain 404)
OAUTH_BODY=$(curl -s --max-time 10 "$SERVER_URL/.well-known/oauth-authorization-server")
assert_contains "GET /.well-known/oauth-authorization-server → oauth_not_supported" \
    "$OAUTH_BODY" '"oauth_not_supported"'

# GET /.well-known/oauth-protected-resource → same guard
OAUTH2_BODY=$(curl -s --max-time 10 "$SERVER_URL/.well-known/oauth-protected-resource")
assert_contains "GET /.well-known/oauth-protected-resource → oauth_not_supported" \
    "$OAUTH2_BODY" '"oauth_not_supported"'

# =============================================================================
# Summary
# =============================================================================
printf "\n"
printf "Results: ${GREEN}%d passed${NC}, ${RED}%d failed${NC}\n" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
