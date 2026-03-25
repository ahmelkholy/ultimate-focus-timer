#!/usr/bin/env python3
"""
Logger - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import setup_logging  # noqa: F401

__all__ = ["setup_logging"]
