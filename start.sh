#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "`start.sh` deprecated. Using uv launcher."

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found."
    echo "Install uv, then run: uv sync"
    exit 1
fi

exec uv run python start-voice.py
