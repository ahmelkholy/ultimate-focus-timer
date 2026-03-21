"""
Centralized logging setup for Ultimate Focus Timer.

Call `setup_logging()` once from main.py before importing other modules.
All other modules should then just use:

    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import logging.handlers

from .app_paths import APP_LOG_FILE, LOG_DIR

_CONSOLE_FORMAT = "%(levelname)-8s %(name)s - %(message)s"
_FILE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO, verbose: bool = False) -> None:
    """
    Configure the root logger with:
      - A StreamHandler on stdout (INFO by default, DEBUG when verbose=True)
      - A RotatingFileHandler writing to log/app.log (always DEBUG)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # gate here; handlers filter further

    if root.handlers:
        # Already configured (e.g. called twice) — skip
        return

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else level)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    for noisy in ("matplotlib", "PIL", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug("Logging initialised (app log: %s)", APP_LOG_FILE)
