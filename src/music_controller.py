#!/usr/bin/env python3
"""
Music Controller - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import MusicController  # noqa: F401

__all__ = ["MusicController"]
