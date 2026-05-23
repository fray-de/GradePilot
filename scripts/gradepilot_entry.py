"""PyInstaller entry point.

Tiny shim that delegates to gradepilot.__main__:main, plus two pieces of
bundle-aware UX:
  - sys.path fixup so `python scripts/gradepilot_entry.py` works in dev
    without `pip install -e .`.
  - Pause-before-exit when the frozen exe owns the console alone (i.e. user
    double-clicked it on Windows). Without this the window closes the moment
    the process exits and the user can't read any output.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gradepilot.__main__ import main  # noqa: E402


def _owns_console_alone() -> bool:
    """True iff this process is the only one attached to its Windows console.

    Double-click → console created for this exe only → count == 1.
    Shell launch → shell is also attached → count >= 2, so we don't pause.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.GetConsoleProcessList.argtypes = [
            ctypes.POINTER(wintypes.DWORD),
            wintypes.DWORD,
        ]
        kernel32.GetConsoleProcessList.restype = wintypes.DWORD
        pids = (wintypes.DWORD * 8)()
        count = kernel32.GetConsoleProcessList(pids, 8)
        return count == 1
    except Exception:
        return False


if __name__ == "__main__":
    code = main()
    if getattr(sys, "frozen", False) and _owns_console_alone():
        try:
            input("\nPress Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(code)
