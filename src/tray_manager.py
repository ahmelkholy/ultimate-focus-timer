#!/usr/bin/env python3
"""
Tray Manager - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import TrayManager  # noqa: F401

__all__ = ["TrayManager"]
