#!/bin/bash
# =============================================================================
# test-uvx.sh — verify: uvx --from <wheel> openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
# shellcheck source=tests/pypi/lib.sh
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd uvx

uv cache prune -q 2>/dev/null || true

run_test 18080 "uvx openapi-mcp-sdk server" \
    uvx --from "$WHEEL" openapi-mcp-sdk server
