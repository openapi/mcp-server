#!/bin/bash
# =============================================================================
# test-pip.sh — verify: pip install <wheel> && openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd pip

VENV_DIR="$(mktemp -d)/venv-pip-test"
info "Creating temp venv: $VENV_DIR"
python3 -m venv "$VENV_DIR"

"$VENV_DIR/bin/pip" install --quiet "$WHEEL"

run_test 18082 "pip install + openapi-mcp-sdk server" \
    "$VENV_DIR/bin/openapi-mcp-sdk" server

rm -rf "$VENV_DIR"
