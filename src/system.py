#!/usr/bin/env python3
"""
system.py - OS-level integrations for Ultimate Focus Timer.

Combines: app_paths, logger, music_controller, notification_manager,
          tray_manager, hotkey_manager
"""

import logging
import logging.handlers
import os
import platform
import signal
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# APP PATHS
# ══════════════════════════════════════════════════════════════════════════════


def _find_project_root() -> Path:
    """Resolve the project root whether running as script or frozen exe."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Running from source: this file lives at <root>/src/system.py
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT: Path = _find_project_root()

SRC_DIR: Path = PROJECT_ROOT / "src"
DATA_DIR: Path = PROJECT_ROOT / "data"
LOG_DIR: Path = PROJECT_ROOT / "log"
EXPORTS_DIR: Path = PROJECT_ROOT / "exports"

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


# ══════════════════════════════════════════════════════════════════════════════
# LOGGER
# ══════════════════════════════════════════════════════════════════════════════

_CONSOLE_FORMAT = "%(levelname)-8s %(name)s - %(message)s"
_FILE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO, verbose: bool = False) -> None:
    """Configure the root logger with a StreamHandler and a RotatingFileHandler."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if root.handlers:
        return  # Already configured

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else level)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))

    file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))

    root.addHandler(console_handler)
    root.addHandler(file_handler)

    for noisy in ("matplotlib", "PIL", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).debug("Logging initialised (app log: %s)", APP_LOG_FILE)


# ══════════════════════════════════════════════════════════════════════════════
# MUSIC CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)

_SUBPROCESS_FLAGS: int = (
    subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
)


class MusicController:
    """Cross-platform music controller using MPV."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.mpv_process: Optional[subprocess.Popen] = None
        self.pid_file: Path = MPV_PID_FILE

        self.mpv_executable: str = self._find_mpv_executable()
        self._mpv_available: bool = self._test_mpv_executable(self.mpv_executable)
        self.current_playlist: Optional[str] = None
        self._paused_playlist: Optional[str] = None
        self.is_playing: bool = False

        logger.debug("MusicController ready (mpv=%s)", self.mpv_executable)

    def _find_mpv_executable(self) -> str:
        configured = self.config.get("mpv_executable", "mpv")
        if self._test_mpv_executable(configured):
            return configured

        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).parent
            for candidate in (
                exe_dir / "mpv.exe",
                exe_dir / "mpv",
                exe_dir / "_internal" / "mpv.exe",
                exe_dir / "_internal" / "mpv",
            ):
                if self._test_mpv_executable(str(candidate)):
                    return str(candidate)

        system = platform.system()
        search_paths: List[str] = []
        if system == "Darwin":
            search_paths = ["/opt/homebrew/bin/mpv", "/usr/local/bin/mpv", "/usr/bin/mpv", "mpv"]
        elif system == "Linux":
            search_paths = ["/usr/bin/mpv", "/usr/local/bin/mpv", "/snap/bin/mpv", "mpv"]
        elif system == "Windows":
            search_paths = [
                "mpv.exe",
                "mpv",
                str(Path.home() / "AppData" / "Local" / "mpv" / "mpv.exe"),
                "C:/Program Files/mpv/mpv.exe",
                "C:/Program Files (x86)/mpv/mpv.exe",
            ]

        for path in search_paths:
            if self._test_mpv_executable(path):
                return path

        logger.warning("MPV executable not found; music will be unavailable")
        return "mpv"

    def _test_mpv_executable(self, path: str) -> bool:
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                timeout=5,
                creationflags=_SUBPROCESS_FLAGS,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def is_mpv_available(self) -> bool:
        return self._mpv_available

    def get_available_playlists(self) -> List[Dict[str, Any]]:
        return self.config.get_music_playlists()

    def _select_default_playlist(self) -> Optional[str]:
        playlists = self.get_available_playlists()
        if not playlists:
            logger.warning("No playlists available")
            return None

        for key in ("classical_music_selected_playlist", "classical_music_default_playlist"):
            configured = self.config.get(key, "")
            if configured:
                for pl in playlists:
                    if pl["path"] == configured or pl["name"] == configured:
                        return pl["path"]

        if self.config.get("classical_music_local_mode", True):
            local = [p for p in playlists if p["type"] == "local"]
            if local:
                return local[0]["path"]

        return playlists[0]["path"]

    def start_music(self, playlist_path: Optional[str] = None, volume: Optional[int] = None) -> bool:
        if not self.is_mpv_available():
            logger.warning("MPV not available; skipping music start")
            return False

        self._stop_process_only()

        if not playlist_path:
            playlist_path = self._paused_playlist or self._select_default_playlist()

        if not playlist_path:
            logger.error("No playlist available to play")
            return False

        if volume is None:
            volume = int(self.config.get("classical_music_volume", 30))

        mpv_args = [
            self.mpv_executable,
            "--no-video",
            "--shuffle",
            "--loop-playlist",
            "--really-quiet",
            f"--volume={volume}",
        ]

        extra = str(self.config.get("mpv_extra_args", "")).strip()
        if extra:
            mpv_args.extend(extra.split())

        mpv_args.append(playlist_path)

        try:
            self.mpv_process = subprocess.Popen(
                mpv_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=_SUBPROCESS_FLAGS,
            )
            self.pid_file.write_text(str(self.mpv_process.pid))
            self.current_playlist = playlist_path
            self._paused_playlist = playlist_path
            self.is_playing = True
            logger.info("Music started (pid=%d, playlist=%s)", self.mpv_process.pid, playlist_path)
            return True
        except OSError:
            logger.exception("Failed to launch MPV")
            return False

    def stop_music(self) -> bool:
        self._stop_process_only()
        self.current_playlist = None
        self._paused_playlist = None
        self.is_playing = False
        return True

    def _stop_process_only(self) -> None:
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                if platform.system() == "Windows":
                    self.mpv_process.terminate()
                else:
                    self.mpv_process.send_signal(signal.SIGTERM)
                try:
                    self.mpv_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.mpv_process.kill()
            except OSError:
                logger.exception("Error terminating MPV process")

        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip())
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True,
                        creationflags=_SUBPROCESS_FLAGS,
                    )
                else:
                    os.kill(pid, signal.SIGTERM)
            except (ValueError, ProcessLookupError, FileNotFoundError):
                pass
            except OSError:
                logger.exception("Error stopping MPV by PID file")
            finally:
                try:
                    self.pid_file.unlink(missing_ok=True)
                except OSError:
                    pass

        self.mpv_process = None

    def pause_music(self) -> bool:
        if not self.is_playing:
            return False
        self._paused_playlist = self.current_playlist
        self._stop_process_only()
        self.current_playlist = None
        self.is_playing = False
        logger.info("Music paused (saved playlist: %s)", self._paused_playlist)
        return True

    def resume_music(self) -> bool:
        if self.is_playing:
            return False
        playlist = self._paused_playlist
        if not playlist:
            logger.warning("No paused playlist to resume; selecting default")
        return self.start_music(playlist_path=playlist)

    def set_volume(self, volume: int) -> bool:
        self.config.set("classical_music_volume", max(0, min(100, volume)))
        if self.is_playing:
            logger.info("Volume updated to %d%% — takes effect on next start", volume)
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_playing": self.is_playing,
            "current_playlist": self.current_playlist,
            "mpv_available": self._mpv_available,
            "volume": self.config.get("classical_music_volume", 30),
        }

    def cleanup(self):
        self.stop_music()


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATION MANAGER
# ══════════════════════════════════════════════════════════════════════════════

try:
    import winsound as _winsound

    _WINSOUND_AVAILABLE = True
except ImportError:
    _winsound = None
    _WINSOUND_AVAILABLE = False

try:
    from plyer import notification as _plyer_notification

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    _plyer_notification = None
    logger.debug("plyer not installed — desktop notifications may be limited")

if platform.system() == "Darwin":
    try:
        import pync as _pync

        PYNC_AVAILABLE = True
    except ImportError:
        _pync = None
        PYNC_AVAILABLE = False
else:
    _pync = None
    PYNC_AVAILABLE = False

MOTIVATIONAL_MESSAGES = {
    "work_start": [
        "Time to focus and make progress!",
        "You've got this! Let's get to work.",
        "Deep focus mode activated!",
        "Every minute counts. Let's do this!",
        "Focus on the task at hand.",
    ],
    "work_complete": [
        "Excellent work! You're building great habits.",
        "Another successful focus session! Keep it up!",
        "Well done! Your productivity is improving.",
        "Great job staying focused!",
        "You're on fire! Keep the momentum going.",
    ],
    "break_start": [
        "Time to recharge and refresh!",
        "Take a well-deserved break.",
        "Rest your mind for a moment.",
        "You've earned this break!",
        "Relax and come back stronger.",
    ],
    "daily_goal": [
        "You're making great progress today!",
        "Keep up the excellent work!",
        "Your focus is paying off!",
        "Productivity level: Outstanding!",
        "You're in the zone today!",
    ],
}


class NotificationManager:
    """Cross-platform notification manager."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.notifications_enabled = self.config.get("desktop_notifications", True)
        self.notification_method = self._get_best_notification_method()

    def _get_best_notification_method(self) -> str:
        system = platform.system()

        if not self.notifications_enabled:
            return "disabled"

        if system == "Windows":
            return "plyer" if PLYER_AVAILABLE else "console"
        elif system == "Darwin":
            if PYNC_AVAILABLE:
                return "pync"
            elif PLYER_AVAILABLE:
                return "plyer"
            else:
                return "osascript"
        elif system == "Linux":
            return "plyer" if PLYER_AVAILABLE else "notify-send"
        else:
            return "console"

    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration: Optional[int] = None,
    ) -> bool:
        if not self.notifications_enabled:
            return False

        if duration is None:
            duration = self.config.get("notification_persistence", 5)

        try:
            if self.notification_method == "disabled":
                return False
            elif self.notification_method == "pync":
                return self._show_pync(title, message, duration)
            elif self.notification_method == "plyer":
                return self._show_plyer(title, message, duration)
            elif self.notification_method == "osascript":
                return self._show_osascript(title, message)
            elif self.notification_method == "notify-send":
                return self._show_notify_send(title, message, duration)
            else:
                return self._show_console(title, message, notification_type)
        except Exception as e:
            logger.warning("Notification error (%s): %s", self.notification_method, e)
            return self._show_console(title, message, notification_type)

    def _show_pync(self, title: str, message: str, duration: int) -> bool:
        try:
            _pync.notify(message, title=title, timeout=duration)
            return True
        except Exception as e:
            logger.warning("pync error: %s", e)
            return False

    def _show_plyer(self, title: str, message: str, duration: int) -> bool:
        try:
            if _plyer_notification is None:
                return False
            _plyer_notification.notify(title=title, message=message, timeout=duration)
            return True
        except Exception as e:
            logger.warning("plyer error: %s", e)
            return False

    def _show_osascript(self, title: str, message: str) -> bool:
        try:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True
        except Exception as e:
            logger.warning("osascript error: %s", e)
            return False

    def _show_notify_send(self, title: str, message: str, duration: int) -> bool:
        try:
            subprocess.run(
                ["notify-send", "-t", str(duration * 1000), title, message],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception as e:
            logger.warning("notify-send error: %s", e)
            return False

    def _show_console(self, title: str, message: str, notification_type: str) -> bool:
        colors = {
            "info": "\033[94m",
            "success": "\033[92m",
            "warning": "\033[93m",
            "error": "\033[91m",
        }
        reset_color = "\033[0m"
        color = colors.get(notification_type, colors["info"])
        print(f"\n{color} {title}{reset_color}")
        print(f"{color} {message}{reset_color}\n")
        return True

    def show_session_start(self, session_type: str, duration: int) -> bool:
        icons = {"work": "🎯", "short_break": "☕", "long_break": "🛋️", "custom": "⏱️"}
        icon = icons.get(session_type, "⏱️")
        title = f"{icon} Focus Session Started"
        message = f"{session_type.replace('_', ' ').title()} session ({duration} min)"
        return self.show_notification(title, message, "info")

    def show_session_complete(self, session_type: str, duration: int) -> bool:
        title = "🎉 Session Complete!"
        message = f"Great work! You completed a {duration}-minute {session_type.replace('_', ' ')} session."
        return self.show_notification(title, message, "success")

    def show_early_warning(self, session_type: str, minutes_remaining: int) -> bool:
        title = "⏰ Time Warning"
        message = f"{minutes_remaining} minute(s) remaining in your {session_type.replace('_', ' ')} session"
        return self.show_notification(title, message, "warning")

    def show_motivational_message(self, message: str) -> bool:
        if not self.config.get("motivational_messages", True):
            return False
        return self.show_notification("💪 Stay Focused!", message, "info")

    def play_completion_sound(self) -> None:
        if not _WINSOUND_AVAILABLE:
            return
        try:
            for freq, duration in [(600, 150), (750, 150), (900, 300)]:
                _winsound.Beep(freq, duration)
        except Exception:
            logger.debug("winsound.Beep failed (may not be supported)")

    def play_start_sound(self) -> None:
        if not _WINSOUND_AVAILABLE:
            return
        try:
            for freq, duration in [(900, 120), (700, 120)]:
                _winsound.Beep(freq, duration)
        except Exception:
            logger.debug("winsound.Beep failed (may not be supported)")

    def enable_notifications(self) -> None:
        self.notifications_enabled = True
        self.config.set("desktop_notifications", True)
        logger.info("Notifications enabled")

    def disable_notifications(self) -> None:
        self.notifications_enabled = False
        self.config.set("desktop_notifications", False)
        logger.info("Notifications disabled")


# ══════════════════════════════════════════════════════════════════════════════
# TRAY MANAGER
# ══════════════════════════════════════════════════════════════════════════════

try:
    import pystray
    from PIL import Image, ImageDraw

    _PYSTRAY_AVAILABLE = True
except ImportError:
    pystray = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
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
        self._thread = None
        self.available = _PYSTRAY_AVAILABLE

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

    def start(self) -> None:
        if not _PYSTRAY_AVAILABLE:
            return
        try:
            import threading
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

    def set_state(self, state: str, tooltip: str = "") -> None:
        if not self._icon:
            return
        color = self._COLORS.get(state, self._COLORS["idle"])
        label = tooltip or f"Focus Timer — {state.title()}"
        try:
            self._icon.icon = _make_icon(color)
            self._icon.title = label
        except Exception:
            logger.exception("Failed to update tray icon state")


# ══════════════════════════════════════════════════════════════════════════════
# HOTKEY MANAGER
# ══════════════════════════════════════════════════════════════════════════════

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
        if not _KEYBOARD_AVAILABLE or not self._registered:
            return
        try:
            keyboard.remove_hotkey(self.HOTKEY_SHOW)
            keyboard.remove_hotkey(self.HOTKEY_PAUSE)
            self._registered = False
            logger.info("Global hotkeys unregistered")
        except Exception:
            logger.exception("Failed to unregister global hotkeys")

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


# ══════════════════════════════════════════════════════════════════════════════
# BRAIN DUMP HOTKEY  (Zeigarnik Offload — Ctrl+Shift+Space)
# ══════════════════════════════════════════════════════════════════════════════

_BRAIN_DUMP_FILE = Path.home() / "brain_dump.md"
_BRAIN_DUMP_HOTKEY = "ctrl+shift+space"

logger_bd = logging.getLogger(__name__)


class BrainDumpHotkey:
    """Registers Ctrl+Shift+Space to instantly capture thoughts to ~/brain_dump.md.

    Pressing the hotkey opens a minimal Tkinter input box.  Whatever the user
    types is appended to ~/brain_dump.md with an ISO timestamp.  The box
    disappears on Enter or Escape so the user can return to work in under two
    seconds.
    """

    def __init__(self, dump_file: Optional[Path] = None) -> None:
        self.dump_file = dump_file or _BRAIN_DUMP_FILE
        self._registered = False

    def start(self) -> None:
        """Register the global hotkey.  Safe to call if keyboard lib is missing."""
        if not _KEYBOARD_AVAILABLE:
            logger_bd.warning("keyboard library not installed — BrainDumpHotkey disabled")
            return
        try:
            keyboard.add_hotkey(_BRAIN_DUMP_HOTKEY, self._open_capture_box)
            self._registered = True
            logger_bd.info("BrainDumpHotkey registered: %s", _BRAIN_DUMP_HOTKEY)
        except Exception:
            logger_bd.exception("Failed to register BrainDumpHotkey")

    def stop(self) -> None:
        if not _KEYBOARD_AVAILABLE or not self._registered:
            return
        try:
            keyboard.remove_hotkey(_BRAIN_DUMP_HOTKEY)
            self._registered = False
        except Exception:
            logger_bd.exception("Failed to unregister BrainDumpHotkey")

    def _open_capture_box(self) -> None:
        """Open a tiny input window in a separate thread to avoid blocking."""
        threading.Thread(target=self._capture_ui, daemon=True).start()

    def _capture_ui(self) -> None:
        """Minimal Tkinter capture window — runs in its own thread."""
        try:
            import tkinter as tk

            root = tk.Tk()
            root.title("Brain Dump")
            root.geometry("500x60+200+200")
            root.attributes("-topmost", True)
            root.configure(bg="#1e1e2e")

            var = tk.StringVar()
            entry = tk.Entry(
                root,
                textvariable=var,
                font=("Courier", 14),
                bg="#313244",
                fg="#cdd6f4",
                insertbackground="#cdd6f4",
                relief="flat",
                bd=8,
            )
            entry.pack(fill="both", expand=True)
            entry.focus_force()

            def _commit(event=None):
                text = var.get().strip()
                if text:
                    self._append_to_file(text)
                root.destroy()

            def _cancel(event=None):
                root.destroy()

            entry.bind("<Return>", _commit)
            entry.bind("<Escape>", _cancel)
            root.mainloop()
        except Exception:
            logger_bd.exception("BrainDumpHotkey capture UI error")

    def _append_to_file(self, text: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"- [{ts}] {text}\n"
        try:
            with open(self.dump_file, "a", encoding="utf-8") as fh:
                fh.write(line)
            logger_bd.debug("Brain dump appended: %s", self.dump_file)
        except OSError:
            logger_bd.exception("Failed to write brain dump")


# ══════════════════════════════════════════════════════════════════════════════
# BINAURAL BEAT GENERATOR  (40 Hz via numpy + sounddevice)
# ══════════════════════════════════════════════════════════════════════════════


class BinauralBeatGenerator:
    """Generates 40 Hz binaural beats using numpy + sounddevice.

    Left channel: carrier_hz
    Right channel: carrier_hz + beat_hz

    The 40 Hz beat frequency is associated with gamma-band neural activity
    and is used as an acoustic neuromodulation tool.
    """

    def __init__(
        self,
        carrier_hz: float = 200.0,
        beat_hz: float = 40.0,
        volume: float = 0.15,
        sample_rate: int = 44100,
    ) -> None:
        self.carrier_hz = carrier_hz
        self.beat_hz = beat_hz
        self.volume = volume
        self.sample_rate = sample_rate

        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.is_playing = False

    def start(self) -> bool:
        """Start binaural beat generation.  Returns False if dependencies missing."""
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
        except ImportError:
            logger_bd.warning("numpy or sounddevice missing — binaural beats disabled")
            return False

        if self.is_playing:
            return True

        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.is_playing = True
        logger_bd.info(
            "Binaural beat started: %.0f Hz carrier + %.0f Hz beat",
            self.carrier_hz,
            self.beat_hz,
        )
        return True

    def stop(self) -> None:
        """Stop the binaural beat generator."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self.is_playing = False
        logger_bd.info("Binaural beat stopped")

    def _loop(self) -> None:
        import numpy as np
        import sounddevice as sd

        block_duration = 0.5
        block_samples = int(self.sample_rate * block_duration)
        sample_idx = 0

        while not self._stop.is_set():
            t = (np.arange(block_samples) + sample_idx) / self.sample_rate
            left = self.volume * np.sin(2 * np.pi * self.carrier_hz * t)
            right = self.volume * np.sin(
                2 * np.pi * (self.carrier_hz + self.beat_hz) * t
            )
            stereo = np.column_stack([left, right]).astype(np.float32)
            try:
                sd.play(stereo, samplerate=self.sample_rate, blocking=True)
            except Exception:
                logger_bd.exception("sounddevice playback error — stopping binaural")
                break
            sample_idx += block_samples
