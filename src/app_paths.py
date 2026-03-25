#!/usr/bin/env python3
"""
App Paths - backward-compat re-export from system.py.
Import from src.system directly for new code.
"""
from .system import (  # noqa: F401
    APP_LOG_FILE,
    CONFIG_FILE,
    DATA_DIR,
    ensure_dirs,
    ERROR_LOG_FILE,
    EXPORTS_DIR,
    LOG_DIR,
    MPV_PID_FILE,
    PROJECT_ROOT,
    SESSION_LOG_FILE,
    SRC_DIR,
    TASKS_FILE,
)

__all__ = [
    "APP_LOG_FILE",
    "CONFIG_FILE",
    "DATA_DIR",
    "ensure_dirs",
    "ERROR_LOG_FILE",
    "EXPORTS_DIR",
    "LOG_DIR",
    "MPV_PID_FILE",
    "PROJECT_ROOT",
    "SESSION_LOG_FILE",
    "SRC_DIR",
    "TASKS_FILE",
]
