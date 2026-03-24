#!/usr/bin/env bash
set -euo pipefail

IS_UBUNTU=false
if [ -f /etc/os-release ] && grep -qi ubuntu /etc/os-release; then
    IS_UBUNTU=true
fi

errors=0

if ! command -v python3 >/dev/null 2>&1; then
    echo "[MISSING] python3 not found."
    if $IS_UBUNTU; then
        echo "            sudo apt update && sudo apt install -y python3"
    else
        echo "            https://www.python.org/downloads/"
    fi
    errors=1
else
    echo "[OK] python3  $(python3 --version)"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "[MISSING] uv not found."
    if $IS_UBUNTU; then
        echo "            curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "            source ~/.bashrc"
    else
        echo "            https://github.com/astral-sh/uv"
        echo "            curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    errors=1
else
    echo "[OK] uv        $(uv --version)"
fi

if [ "$errors" -eq 0 ]; then
    echo ""
    echo "Environment OK."
else
    echo ""
    echo "Fix the issues above, then run 'make check-env' again."
    exit 1
fi
