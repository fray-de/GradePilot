"""PyInstaller entry point.

Tiny shim that delegates to gradepilot.__main__:main, plus two pieces of
bundle-aware UX:
  - sys.path fixup so `python scripts/gradepilot_entry.py` works in dev
    without `pip install -e .`.
  - Pause-before-exit when the frozen exe is talking to a terminal. We use
    a simple stdout-is-a-tty check rather than GetConsoleProcessList — the
    latter doesn't reliably distinguish "double-click" from "shell launch"
    under Windows Terminal / ConPTY. Cost: shell users press Enter once
    per invocation. Benefit: double-clicked output never vanishes.
    Pipes/redirects (e.g. `gradepilot.exe --version > out.txt`) skip the
    pause because stdout isn't a tty there.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gradepilot.__main__ import main  # noqa: E402


def _should_pause() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    try:
        return sys.stdout.isatty()
    except (AttributeError, ValueError, OSError):
        return True  # err on the side of pausing, never on vanishing


if __name__ == "__main__":
    code = main()
    if _should_pause():
        try:
            input("\nPress Enter to exit...")
        except (EOFError, KeyboardInterrupt, OSError):
            pass
    sys.exit(code)
