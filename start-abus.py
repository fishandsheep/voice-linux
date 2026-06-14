from __future__ import annotations

import subprocess
import sys


def main() -> int:
    args = sys.argv[1:]
    app_name = args[0] if args else "voice"
    is_update = "--update" in args[1:]

    if app_name != "voice":
        print(f"Unsupported app `{app_name}`.")
        print("Use `uv run python start-voice.py` for Voice-Pro.")
        return 1

    print("`start-abus.py` deprecated. Forwarding to `uv`.")

    if is_update:
        return subprocess.run(["uv", "sync", "--upgrade"]).returncode

    return subprocess.run(["uv", "run", "python", "start-voice.py"]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
