"""
Ultimate Focus Timer Package
A comprehensive cross-platform productivity timer application.
"""

from .__version__ import __author__, __description__, __version__

__all__ = [
    "ConfigManager",
    "MusicController",
    "NotificationManager",
    "SessionManager",
    "TaskManager",
    "__author__",
    "__description__",
    "__version__",
]

# Lazy imports — failures are logged, not silently swallowed
try:
    from .core import ConfigManager, SessionManager, TaskManager
    from .system import MusicController, NotificationManager
except ImportError as _exc:
    import logging

    logging.getLogger(__name__).warning("Core import error: %s", _exc)
