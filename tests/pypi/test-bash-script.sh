#!/bin/bash
# =============================================================================
# test-bash-script.sh — verify the mcp-server.sh one-click launcher pattern
# Uses uvx under the hood (same as the documented quick start)
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd uvx

# Build a launcher script identical to what the README instructs users to create
LAUNCHER="$(mktemp)"
cat > "$LAUNCHER" << SCRIPT
#!/bin/bash
export PORT=18084
export SERVICES_CREDENTIALS="\${SERVICES_CREDENTIALS:-{}}"
uvx --from "$WHEEL" openapi-mcp-sdk server
SCRIPT
chmod +x "$LAUNCHER"

run_test 18084 "bash mcp-server.sh (launcher script pattern)" \
    bash "$LAUNCHER"

rm -f "$LAUNCHER"
