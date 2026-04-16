#!/bin/bash
# =============================================================================
# test-pip.sh — verify: pip install <wheel> && openapi-mcp-sdk server
# =============================================================================
set -euo pipefail
# shellcheck source=tests/pypi/lib.sh
source "$(dirname "$0")/lib.sh"

require_wheel
require_cmd pip

PYTHON=$(uv python find 3.13 2>/dev/null || python3.13 2>/dev/null || echo "")
if [[ -z "$PYTHON" ]]; then
    info "Skipping — Python 3.13 not found (package requires >=3.13)"
    exit 0
fi

VENV_DIR="$(mktemp -d)/venv-pip-test"
info "Creating temp venv with $PYTHON: $VENV_DIR"
"$PYTHON" -m venv "$VENV_DIR"

"$VENV_DIR/bin/pip" install --quiet "$WHEEL"

run_test 18082 "pip install + openapi-mcp-sdk server" \
    "$VENV_DIR/bin/openapi-mcp-sdk" server

rm -rf "$VENV_DIR"
