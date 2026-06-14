#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "`configure.sh` deprecated. Linux NVIDIA flow now uses uv."
echo "System deps still need manual install: git, ffmpeg, build-essential, espeak-ng."

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found."
    echo "Install uv first: https://docs.astral.sh/uv/"
    exit 1
fi

exec uv sync
