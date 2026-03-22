"""
System tray icon for Ultimate Focus Timer.

Uses pystray + Pillow to show a colour-coded icon in the system tray:
  Red    = work session running
  Blue   = break session running
  Orange = paused
  Grey   = idle
"""

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)

try:
    import pystray
    from PIL import Image, ImageDraw

    _PYSTRAY_AVAILABLE = True
except ImportError:
    pystray = None  # type: ignore[assignment]
    Image = None    # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    _PYSTRAY_AVAILABLE = False
    logger.warning("pystray/Pillow not installed — system tray disabled")

_ICON_SIZE = 64


def _make_icon(color: str) -> "Image.Image":
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, _ICON_SIZE - 4, _ICON_SIZE - 4], fill=color)
    return img


class TrayManager:
    """Manages the system tray icon and right-click context menu."""

    _COLORS = {
        "work": "#e74c3c",
        "break": "#3498db",
        "paused": "#f39c12",
        "idle": "#808080",
    }

    def __init__(
        self,
        on_show: Optional[Callable] = None,
        on_start_work: Optional[Callable] = None,
        on_start_break: Optional[Callable] = None,
        on_pause_resume: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_quit: Optional[Callable] = None,
    ):
        self._on_show = on_show
        self._on_start_work = on_start_work
        self._on_start_break = on_start_break
        self._on_pause_resume = on_pause_resume
        self._on_stop = on_stop
        self._on_quit = on_quit
        self._icon: Optional["pystray.Icon"] = None
        self._thread: Optional[threading.Thread] = None
        self.available = _PYSTRAY_AVAILABLE

    # ── Menu construction ──────────────────────────────────────────────────────

    def _build_menu(self) -> "pystray.Menu":
        def _call(fn):
            def _handler(icon, item):
                if fn:
                    fn()

            return _handler

        return pystray.Menu(
            pystray.MenuItem("Show Window", _call(self._on_show), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Work Session", _call(self._on_start_work)),
            pystray.MenuItem("Start Break Session", _call(self._on_start_break)),
            pystray.MenuItem("Pause / Resume", _call(self._on_pause_resume)),
            pystray.MenuItem("Stop Session", _call(self._on_stop)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _call(self._quit_from_tray)),
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Create and run the tray icon in a background daemon thread."""
        if not _PYSTRAY_AVAILABLE:
            return
        try:
            self._icon = pystray.Icon(
                "FocusTimer",
                _make_icon(self._COLORS["idle"]),
                "Focus Timer — Idle",
                self._build_menu(),
            )
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()
            logger.info("System tray icon started")
        except Exception:
            logger.exception("Failed to start system tray icon")

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def _quit_from_tray(self) -> None:
        self.stop()
        if self._on_quit:
            self._on_quit()

    # ── State updates ──────────────────────────────────────────────────────────

    def set_state(self, state: str, tooltip: str = "") -> None:
        """Update icon colour and tooltip.

        state — one of: 'work', 'break', 'paused', 'idle'
        """
        if not self._icon:
            return
        color = self._COLORS.get(state, self._COLORS["idle"])
        label = tooltip or f"Focus Timer — {state.title()}"
        try:
            self._icon.icon = _make_icon(color)
            self._icon.title = label
        except Exception:
            logger.exception("Failed to update tray icon state")
