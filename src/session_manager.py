#!/usr/bin/env python3
"""
Session Manager - backward-compat re-export from core.py.
Import from src.core directly for new code.
"""
from .core import (  # noqa: F401
    SessionManager,
    SessionState,
    SessionType,
)

__all__ = ["SessionManager", "SessionState", "SessionType"]
