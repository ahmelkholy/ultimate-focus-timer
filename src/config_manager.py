#!/usr/bin/env python3
"""
Configuration Manager - backward-compat re-export from core.py.
Import from src.core directly for new code.
"""
from .core import (  # noqa: F401
    AppConfig,
    ConfigManager,
    DEFAULT_CONFIG,
    MusicConfig,
    NotificationConfig,
    TimerConfig,
    get_config,
)

__all__ = [
    "AppConfig",
    "ConfigManager",
    "DEFAULT_CONFIG",
    "MusicConfig",
    "NotificationConfig",
    "TimerConfig",
    "get_config",
]
