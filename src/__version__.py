"""
Ultimate Focus Timer Version Information
"""

__version__ = "1.0.0"
__author__ = "Ultimate Focus Timer Team"
__email__ = "contact@ultimatefocustimer.com"
__description__ = "A comprehensive cross-platform productivity timer application"
__url__ = "https://github.com/yourusername/ultimate-focus-timer"

# Version components
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_INFO = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

# Build and release information
BUILD_DATE = "2025-06-08"
RELEASE_CHANNEL = "stable"

def get_version():
    """Return the version string."""
    return __version__

def get_version_info():
    """Return the version as a tuple."""
    return VERSION_INFO
