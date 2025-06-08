"""
Ultimate Focus Timer Package
A comprehensive cross-platform productivity timer application
"""

from .__version__ import __version__, __author__, __description__

__all__ = [
    '__version__',
    '__author__',
    '__description__',
    'ConfigManager',
    'SessionManager',
    'MusicController',
    'NotificationManager',
    'FocusGUI',
    'FocusConsole',
    'Dashboard',
    'CLI'
]

# Import main components for easy access
try:
    from .config_manager import ConfigManager
    from .session_manager import SessionManager
    from .music_controller import MusicController
    from .notification_manager import NotificationManager
    from .focus_gui import FocusGUI
    from .focus_console import FocusConsole
    from .dashboard import Dashboard
    from .cli import CLI
except ImportError:
    # Handle import errors gracefully during development
    pass
