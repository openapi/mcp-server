#!/bin/bash
# =============================================================================
# test-pip3.sh — verify: pip3 install <wheel> && openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
# shellcheck source=tests/pypi/lib.sh
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd pip3

PYTHON=$(uv python find 3.13 2>/dev/null || python3.13 2>/dev/null || echo "")
if [[ -z "$PYTHON" ]]; then
    info "Skipping — Python 3.13 not found (package requires >=3.13)"
    exit 0
fi

VENV_DIR="$(mktemp -d)/venv-pip3-test"
info "Creating temp venv with $PYTHON: $VENV_DIR"
"$PYTHON" -m venv "$VENV_DIR"

"$VENV_DIR/bin/pip3" install --quiet "$WHEEL"

run_test 18083 "pip3 install + openapi-mcp-sdk server" \
    "$VENV_DIR/bin/openapi-mcp-sdk" server

rm -rf "$VENV_DIR"
