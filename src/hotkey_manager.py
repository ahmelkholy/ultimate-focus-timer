#!/usr/bin/env python3
"""
Hotkey Manager - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import HotkeyManager  # noqa: F401

__all__ = ["HotkeyManager"]
