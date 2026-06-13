#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_PYTHON="$SCRIPT_DIR/installer_files/env/bin/python"
LOG_FILE="${VOICE_PRO_LOG:-/tmp/voice-pro.log}"
PID_FILE="${VOICE_PRO_PID:-/tmp/voice-pro.pid}"

if [ ! -x "$ENV_PYTHON" ]; then
    echo "Missing environment: $ENV_PYTHON"
    echo "Run ./start.sh once to create installer_files/env."
    exit 1
fi

if [ -f "$PID_FILE" ]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "${OLD_PID:-}" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "voice-pro already running on pid $OLD_PID"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

NVIDIA_LIB_PATH="$("$ENV_PYTHON" - <<'PY'
import os

paths = []

try:
    import nvidia.cublas.lib

    paths.append(os.path.dirname(nvidia.cublas.lib.__file__))
except ImportError:
    pass

try:
    import nvidia.cudnn.lib

    paths.append(os.path.dirname(nvidia.cudnn.lib.__file__))
except ImportError:
    pass

print(":".join(paths))
PY
)"

if [ -n "$NVIDIA_LIB_PATH" ]; then
    if [ -n "${LD_LIBRARY_PATH:-}" ]; then
        export LD_LIBRARY_PATH="$NVIDIA_LIB_PATH:$LD_LIBRARY_PATH"
    else
        export LD_LIBRARY_PATH="$NVIDIA_LIB_PATH"
    fi
fi

setsid "$ENV_PYTHON" start-voice.py >"$LOG_FILE" 2>&1 < /dev/null &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 8

if kill -0 "$PID" 2>/dev/null; then
    echo "voice-pro started"
    echo "pid: $PID"
    echo "url: http://127.0.0.1:7860"
    echo "log: $LOG_FILE"
else
    echo "voice-pro failed to start"
    echo "log: $LOG_FILE"
    exit 1
fi
