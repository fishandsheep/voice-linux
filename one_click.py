from __future__ import annotations

import sys


def main() -> int:
    print("`one_click.py` deprecated.")
    print("Use `uv sync` to install dependencies.")
    print("Use `uv run python start-voice.py` to launch Voice-Pro.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
