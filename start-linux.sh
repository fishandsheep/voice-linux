#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="${VOICE_PRO_LOG:-/tmp/voice-pro.log}"
PID_FILE="${VOICE_PRO_PID:-/tmp/voice-pro.pid}"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found."
    echo "Install uv, then run: uv sync"
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

setsid uv run python start-voice.py >"$LOG_FILE" 2>&1 < /dev/null &
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
