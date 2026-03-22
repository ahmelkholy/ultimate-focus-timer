"""
focus.pyw — Windowless double-click launcher for the Focus Timer.

Windows associates .pyw files with pythonw.exe, so double-clicking this file
opens the GUI without any console window.  All logging still goes to log/app.log.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so `src.*` imports resolve correctly.
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

# Inject --gui if caller didn't pass any arguments (plain double-click)
if (
    "--gui" not in sys.argv
    and "--console" not in sys.argv
    and "--dashboard" not in sys.argv
):
    sys.argv.append("--gui")

# Run main entry point
from main import main  # noqa: E402

main()
