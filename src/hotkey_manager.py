"""
Global hotkey manager for Ultimate Focus Timer.

Registers system-wide keyboard shortcuts using the `keyboard` library:
  Ctrl+Alt+F  — show / raise the main window
  Ctrl+Alt+P  — pause / resume the current session
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    import keyboard

    _KEYBOARD_AVAILABLE = True
except ImportError:
    _KEYBOARD_AVAILABLE = False
    logger.warning("keyboard library not installed — global hotkeys disabled")


class HotkeyManager:
    """Registers and manages system-wide hotkeys."""

    HOTKEY_SHOW = "ctrl+alt+f"
    HOTKEY_PAUSE = "ctrl+alt+p"

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_pause_resume: Optional[Callable] = None,
    ):
        self._on_show = on_show
        self._on_pause_resume = on_pause_resume
        self._registered = False
        self.available = _KEYBOARD_AVAILABLE

    def start(self) -> None:
        """Register global hotkeys.  Safe to call even if library is missing."""
        if not _KEYBOARD_AVAILABLE:
            return
        try:
            keyboard.add_hotkey(self.HOTKEY_SHOW, self._handle_show)
            keyboard.add_hotkey(self.HOTKEY_PAUSE, self._handle_pause_resume)
            self._registered = True
            logger.info(
                "Global hotkeys registered: %s (show), %s (pause/resume)",
                self.HOTKEY_SHOW,
                self.HOTKEY_PAUSE,
            )
        except Exception:
            logger.exception("Failed to register global hotkeys")

    def stop(self) -> None:
        """Unregister all hotkeys."""
        if not _KEYBOARD_AVAILABLE or not self._registered:
            return
        try:
            keyboard.remove_hotkey(self.HOTKEY_SHOW)
            keyboard.remove_hotkey(self.HOTKEY_PAUSE)
            self._registered = False
            logger.info("Global hotkeys unregistered")
        except Exception:
            logger.exception("Failed to unregister global hotkeys")

    # ── Internal handlers ──────────────────────────────────────────────────────

    def _handle_show(self) -> None:
        if self._on_show:
            try:
                self._on_show()
            except Exception:
                logger.exception("Error in hotkey show handler")

    def _handle_pause_resume(self) -> None:
        if self._on_pause_resume:
            try:
                self._on_pause_resume()
            except Exception:
                logger.exception("Error in hotkey pause/resume handler")
