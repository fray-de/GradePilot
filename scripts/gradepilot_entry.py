"""PyInstaller entry point.

PyInstaller treats this file as a top-level script and follows its imports.
Keep it tiny — just delegate to gradepilot.__main__.main(). The gradepilot
package itself must be importable, which the workflow ensures via
`pip install -e .` before invoking PyInstaller.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the gradepilot package importable when running this script directly
# (e.g. local dev). In CI the package is pip-installed editable, so this
# is a no-op there.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gradepilot.__main__ import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
