#!/usr/bin/env python3
"""
Notification Manager - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import (  # noqa: F401
    MOTIVATIONAL_MESSAGES,
    NotificationManager,
)

__all__ = ["MOTIVATIONAL_MESSAGES", "NotificationManager"]
