#!/bin/bash
# =============================================================================
# test-pipx.sh — verify: pipx run --spec <wheel> openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
# shellcheck source=tests/pypi/lib.sh
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd pipx

run_test 18081 "pipx run openapi-mcp-sdk server" \
    pipx run --spec "$WHEEL" openapi-mcp-sdk server
