#!/usr/bin/env python3
"""Windowed GUI entry point for packaged installs."""

from __future__ import annotations

import os


def main() -> None:
    """Launch the Tkinter GUI without requiring command-line flags."""
    os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

    from main import _detach_gui_on_windows, UltimateFocusLauncher

    _detach_gui_on_windows()
    UltimateFocusLauncher().launch_gui()


if __name__ == "__main__":
    main()
