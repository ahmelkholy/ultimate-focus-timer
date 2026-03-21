"""
Centralized path resolution for Ultimate Focus Timer.

All paths are anchored to PROJECT_ROOT so they are consistent
regardless of the working directory or PyInstaller packaging.
"""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    """Resolve the project root whether running as script or frozen exe."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundles everything relative to the executable
        return Path(sys.executable).resolve().parent
    # Running from source: this file lives at <root>/src/app_paths.py
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT: Path = _find_project_root()

# ── Fixed directories ──────────────────────────────────────────────────────────
SRC_DIR: Path = PROJECT_ROOT / "src"
DATA_DIR: Path = PROJECT_ROOT / "data"
LOG_DIR: Path = PROJECT_ROOT / "log"
EXPORTS_DIR: Path = PROJECT_ROOT / "exports"

# ── Key files ─────────────────────────────────────────────────────────────────
CONFIG_FILE: Path = PROJECT_ROOT / "config.yml"
TASKS_FILE: Path = DATA_DIR / "daily_tasks.json"
SESSION_LOG_FILE: Path = LOG_DIR / "focus.log"
APP_LOG_FILE: Path = LOG_DIR / "app.log"
ERROR_LOG_FILE: Path = PROJECT_ROOT / "error.log"
MPV_PID_FILE: Path = PROJECT_ROOT / "mpv_classical.pid"


def ensure_dirs() -> None:
    """Create required runtime directories if they don't exist."""
    for directory in (DATA_DIR, LOG_DIR, EXPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
