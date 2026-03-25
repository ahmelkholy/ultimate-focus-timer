#!/usr/bin/env python3
"""
Task Manager - backward-compat re-export from core.py.
Import from src.core directly for new code.
"""
from .core import (  # noqa: F401
    Task,
    TaskManager,
)

__all__ = ["Task", "TaskManager"]
