#!/bin/bash
# =============================================================================
# tests/pypi/run-all.sh — run all PyPI package smoke tests
#
# Usage:
#   bash tests/pypi/run-all.sh
#
# What it does:
#   1. Builds the package (uv build) if dist/ is empty or stale
#   2. Runs each test-*.sh in sequence
#   3. Reports a final pass/fail summary
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- colours ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'

section() { echo -e "\n${BOLD}$*${RESET}"; }
info()    { echo -e "${YELLOW}  INFO${RESET}  $*"; }

# ---------------------------------------------------------------------------
# 1. Build the package if needed
# ---------------------------------------------------------------------------
section "=== Building package ==="
cd "$REPO_ROOT"
uv build 2>&1 | tail -4

WHEEL="$(find "$REPO_ROOT/dist" -maxdepth 1 -type f -name 'openapi_mcp_sdk-*.whl' 2>/dev/null | sort -V | tail -1)"
if [[ -z "$WHEEL" ]]; then
    echo -e "${RED}ERROR${RESET} wheel not found after build"
    exit 1
fi
info "Wheel: $(basename "$WHEEL")"

# ---------------------------------------------------------------------------
# 2. Run each test-*.sh
# ---------------------------------------------------------------------------
section "=== Running tests ==="

PASS=0
FAIL=0
RESULTS=()

for test_script in "$SCRIPT_DIR"/test-*.sh; do
    name="$(basename "$test_script")"
    echo ""
    echo -e "${BOLD}── $name${RESET}"

    set +e
    bash "$test_script"
    exit_code=$?
    set -e

    case $exit_code in
        0)  (( PASS++ )); RESULTS+=("${GREEN}PASS${RESET}  $name") ;;
        *)  (( FAIL++ )); RESULTS+=("${RED}FAIL${RESET}  $name (exit $exit_code)") ;;
    esac
done

# ---------------------------------------------------------------------------
# 3. Summary
# ---------------------------------------------------------------------------
section "=== Summary ==="
for r in "${RESULTS[@]}"; do
    echo -e "  $r"
done
echo ""
echo -e "  Total: ${GREEN}$PASS passed${RESET}  ${RED}$FAIL failed${RESET}"

[[ $FAIL -eq 0 ]]
