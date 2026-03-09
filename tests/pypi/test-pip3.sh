#!/bin/bash
# =============================================================================
# test-pip3.sh — verify: pip3 install <wheel> && openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd pip3

VENV_DIR="$(mktemp -d)/venv-pip3-test"
info "Creating temp venv: $VENV_DIR"
python3 -m venv "$VENV_DIR"

"$VENV_DIR/bin/pip3" install --quiet "$WHEEL"

run_test 18083 "pip3 install + openapi-mcp-sdk server" \
    "$VENV_DIR/bin/openapi-mcp-sdk" server

rm -rf "$VENV_DIR"
