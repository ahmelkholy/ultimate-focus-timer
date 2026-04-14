#!/usr/bin/env python3
"""
core.py - Pure Python backend for Ultimate Focus Timer.

Combines: config_manager, session_manager, task_manager
"""

import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .google_integration import DEFAULT_TASK_LIST_ID, GoogleIntegration
from .system import (
    CONFIG_FILE,
    DATA_DIR,
    LOG_DIR,
    PROJECT_ROOT,
    SESSION_LOG_FILE,
    TASKS_FILE,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class TimerConfig:
    work_duration: int = 25
    short_break_duration: int = 5
    long_break_duration: int = 15
    sessions_until_long_break: int = 4
    auto_start_breaks: bool = True
    auto_start_work: bool = False
    auto_start_delay: int = 2
    min_work_time: int = 5
    max_daily_sessions: int = 0


@dataclass
class MusicConfig:
    enabled: bool = True
    volume: int = 30
    shuffle: bool = True
    repeat: bool = True
    local_mode: bool = True
    pause_on_break: bool = True
    mpv_path: str = "mpv"
    extra_args: str = ""
    default_playlist: str = ""
    playlist_dir: str = ""
    online_playlists: List[str] = field(default_factory=list)
    fade_transitions: bool = True


@dataclass
class NotificationConfig:
    enabled: bool = True
    sound: bool = True
    desktop: bool = True
    early_warning_mins: int = 2
    priority: str = "normal"
    persistence_secs: int = 5
    motivational: bool = True


@dataclass
class AppConfig:
    color_scheme: str = "forest"
    accent_color: str = "#00ff00"
    dark_theme: bool = True
    animated_transitions: bool = True
    productivity_scoring: bool = True
    session_goals: int = 8
    weekly_goals: int = 40
    data_retention_days: int = 365
    task_file: str = "~/tasks.md"
    window_geometry: str = ""


DEFAULT_CONFIG: Dict[str, Any] = {
    "work_mins": 25,
    "short_break_mins": 5,
    "long_break_mins": 15,
    "long_break_interval": 4,
    "work_msg": "Focus on your task",
    "short_break_msg": "Take a breather",
    "long_break_msg": "Take a long break",
    "notify": True,
    "notify_sound": True,
    "notify_early_warning": 2,
    "desktop_notifications": True,
    "notification_priority": "normal",
    "motivational_messages": True,
    "notification_persistence": 5,
    "auto_start_work": False,
    "auto_start_break": True,
    "auto_start_delay": 2,
    "resume_incomplete": True,
    "save_incomplete": True,
    "max_daily_sessions": 0,
    "min_work_time": 5,
    "smart_break_adjustment": True,
    "deep_focus_mode": False,
    "productivity_scoring": True,
    "session_goals": 8,
    "weekly_goals": 40,
    "24hr_clock": False,
    "show_seconds": True,
    "show_progress_bar": True,
    "sound": "",
    "sound_volume": 100,
    "sound_on_break": False,
    "fade_sound": True,
    "classical_music": True,
    "classical_music_volume": 30,
    "classical_music_shuffle": True,
    "classical_music_repeat": True,
    "classical_music_local_mode": True,
    "classical_music_default_playlist": "",
    "classical_music_selected_playlist": "",
    "classical_music_playlist_dir": "",
    "classical_music_online_playlists": [
        "https://www.youtube.com/playlist?list=PLRBp0Fe2GpgmgL97AviPkenNzgzHByGgs",
        "https://www.youtube.com/playlist?list=PLcNiN7SthNjHqrGWzTsJq1OAZ8TUQgOfO",
        "https://www.youtube.com/playlist?list=PLTKWrxUB7R8SYCcrfHONp9QbdA3-CKx6p",
    ],
    "mpv_executable": "mpv",
    "mpv_extra_args": "",
    "fade_music_transitions": True,
    "pause_music_on_break": True,
    "classical_music_genres": ["baroque", "classical", "romantic", "modern"],
    "dark_theme": True,
    "accent_color": "#00ff00",
    "compact_mode": False,
    "animated_transitions": True,
    "gradient_backgrounds": True,
    "transparency": 0.95,
    "blur_background": True,
    "color_scheme": "forest",
    "custom_css": "",
    "track_idle_time": True,
    "auto_tags": True,
    "stats_default_view": "week",
    "export_format": "csv",
    "detailed_analytics": True,
    "productivity_trends": True,
    "session_quality_rating": True,
    "distraction_tracking": True,
    "time_blocking": True,
    "goal_tracking": True,
    "weekly_reports": True,
    "data_retention_days": 365,
    "todo_integration": False,
    "task_file": "~/tasks.md",
    "auto_task_complete": True,
    "window_geometry": "",
}


class ConfigManager:
    """Loads application configuration from YAML and provides typed accessors."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path: Path = config_path or CONFIG_FILE
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self) -> None:
        if not self.config_path.exists():
            logger.warning(
                "Config file not found: %s — using defaults", self.config_path
            )
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                file_cfg = yaml.safe_load(fh) or {}
            self.config.update(file_cfg)
            self._normalise_paths()
            logger.debug("Configuration loaded from %s", self.config_path)
        except yaml.YAMLError as exc:
            logger.error(
                "YAML parse error in %s: %s — using defaults", self.config_path, exc
            )
        except OSError as exc:
            logger.error(
                "Cannot read config %s: %s — using defaults", self.config_path, exc
            )

    def load_config(self) -> None:
        """Reload configuration from disk (alias used by GUI after settings save)."""
        self.config = DEFAULT_CONFIG.copy()
        self._load()

    def _normalise_paths(self) -> None:
        for key in (
            "classical_music_default_playlist",
            "classical_music_selected_playlist",
            "classical_music_playlist_dir",
            "task_file",
        ):
            raw = self.config.get(key)
            if raw:
                self.config[key] = str(Path(raw).expanduser())

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    def save_config(self) -> bool:
        try:
            with open(self.config_path, "w", encoding="utf-8") as fh:
                yaml.dump(self.config, fh, default_flow_style=False, sort_keys=True)
            logger.debug("Configuration saved to %s", self.config_path)
            return True
        except OSError as exc:
            logger.error("Error saving config: %s", exc)
            return False

    def get_timer_config(self) -> TimerConfig:
        c = self.config
        return TimerConfig(
            work_duration=int(c.get("work_mins", 25)),
            short_break_duration=int(c.get("short_break_mins", 5)),
            long_break_duration=int(c.get("long_break_mins", 15)),
            sessions_until_long_break=int(c.get("long_break_interval", 4)),
            auto_start_breaks=bool(c.get("auto_start_break", True)),
            auto_start_work=bool(c.get("auto_start_work", False)),
            auto_start_delay=int(c.get("auto_start_delay", 2)),
            min_work_time=int(c.get("min_work_time", 5)),
            max_daily_sessions=int(c.get("max_daily_sessions", 0)),
        )

    def get_music_config(self) -> MusicConfig:
        c = self.config
        return MusicConfig(
            enabled=bool(c.get("classical_music", True)),
            volume=int(c.get("classical_music_volume", 30)),
            shuffle=bool(c.get("classical_music_shuffle", True)),
            repeat=bool(c.get("classical_music_repeat", True)),
            local_mode=bool(c.get("classical_music_local_mode", True)),
            pause_on_break=bool(c.get("pause_music_on_break", True)),
            mpv_path=str(c.get("mpv_executable", "mpv")),
            extra_args=str(c.get("mpv_extra_args", "")),
            default_playlist=str(c.get("classical_music_default_playlist", "")),
            playlist_dir=str(c.get("classical_music_playlist_dir", "")),
            online_playlists=list(c.get("classical_music_online_playlists", [])),
            fade_transitions=bool(c.get("fade_music_transitions", True)),
        )

    def get_notification_config(self) -> NotificationConfig:
        c = self.config
        return NotificationConfig(
            enabled=bool(c.get("notify", True)),
            sound=bool(c.get("notify_sound", True)),
            desktop=bool(c.get("desktop_notifications", True)),
            early_warning_mins=int(c.get("notify_early_warning", 2)),
            priority=str(c.get("notification_priority", "normal")),
            persistence_secs=int(c.get("notification_persistence", 5)),
            motivational=bool(c.get("motivational_messages", True)),
        )

    def get_app_config(self) -> AppConfig:
        c = self.config
        return AppConfig(
            color_scheme=str(c.get("color_scheme", "forest")),
            accent_color=str(c.get("accent_color", "#00ff00")),
            dark_theme=bool(c.get("dark_theme", True)),
            animated_transitions=bool(c.get("animated_transitions", True)),
            productivity_scoring=bool(c.get("productivity_scoring", True)),
            session_goals=int(c.get("session_goals", 8)),
            weekly_goals=int(c.get("weekly_goals", 40)),
            data_retention_days=int(c.get("data_retention_days", 365)),
            task_file=str(c.get("task_file", "~/tasks.md")),
            window_geometry=str(c.get("window_geometry", "")),
        )

    def get_music_playlists(self) -> List[Dict[str, str]]:
        playlists: List[Dict[str, str]] = []
        mc = self.get_music_config()

        if mc.default_playlist and Path(mc.default_playlist).exists():
            playlists.append(
                {
                    "name": "Default Classical Music",
                    "path": mc.default_playlist,
                    "type": "local",
                }
            )

        if mc.playlist_dir and Path(mc.playlist_dir).is_dir():
            for pf in Path(mc.playlist_dir).glob("*.m3u*"):
                playlists.append({"name": pf.stem, "path": str(pf), "type": "local"})

        if not mc.local_mode:
            for i, url in enumerate(mc.online_playlists):
                playlists.append(
                    {"name": f"Online Playlist {i + 1}", "path": url, "type": "online"}
                )

        return playlists

    def validate_config(self) -> List[str]:
        issues: List[str] = []
        tc = self.get_timer_config()
        mc = self.get_music_config()

        for name, val, lo, hi in [
            ("work_mins", tc.work_duration, 1, 120),
            ("short_break_mins", tc.short_break_duration, 1, 60),
            ("long_break_mins", tc.long_break_duration, 1, 120),
            ("classical_music_volume", mc.volume, 0, 100),
            ("sound_volume", int(self.config.get("sound_volume", 100)), 0, 100),
        ]:
            if not (lo <= val <= hi):
                issues.append(f"{name} must be between {lo} and {hi} (got {val})")

        if mc.default_playlist and not Path(mc.default_playlist).exists():
            issues.append(f"Default playlist not found: {mc.default_playlist}")

        return issues

    def update_timer_config(self, timer_config: Dict[str, Any]) -> None:
        mapping = {
            "work_duration": "work_mins",
            "short_break_duration": "short_break_mins",
            "long_break_duration": "long_break_mins",
            "sessions_until_long_break": "long_break_interval",
            "auto_start_breaks": "auto_start_break",
            "auto_start_work": "auto_start_work",
            "min_work_time": "min_work_time",
            "max_daily_sessions": "max_daily_sessions",
        }
        for new_key, old_key in mapping.items():
            if new_key in timer_config:
                self.set(old_key, timer_config[new_key])

    def __str__(self) -> str:
        return f"ConfigManager(path={self.config_path}, keys={len(self.config)})"


_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


# ══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGER
# ══════════════════════════════════════════════════════════════════════════════

_STATE_FILE = PROJECT_ROOT / ".session.state"
_AUTO_SAVE_INTERVAL = 10  # seconds


class SessionType(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    CUSTOM = "custom"


class SessionState(Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class SessionManager:
    """Pure headless timer engine.  Business logic only — no UI, no audio."""

    def __init__(self, config_manager):
        self.config = config_manager

        self.session_type = SessionType.WORK
        self.session_duration: int = 0
        self.elapsed_seconds: int = 0
        self.state = SessionState.READY
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None

        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = running, clear = paused

        self._cb_session_start: Optional[Callable] = None
        self._cb_tick: Optional[Callable] = None
        self._cb_complete: Optional[Callable] = None
        self._cb_state_change: Optional[Callable] = None
        self._cb_early_warning: Optional[Callable] = None
        self._cb_pause: Optional[Callable] = None
        self._cb_resume: Optional[Callable] = None
        self._cb_stop: Optional[Callable] = None

        self.completed_work_sessions: int = 0
        self.session_count: int = 0

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = SESSION_LOG_FILE

        self._auto_save_thread: Optional[threading.Thread] = None
        self._auto_save_stop = threading.Event()

        logger.debug("SessionManager ready (log=%s)", self.log_file)

    def set_callbacks(
        self,
        on_tick: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
        on_session_start: Optional[Callable] = None,
        on_early_warning: Optional[Callable] = None,
        on_pause: Optional[Callable] = None,
        on_resume: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
    ):
        if on_tick is not None:
            self._cb_tick = on_tick
        if on_complete is not None:
            self._cb_complete = on_complete
        if on_state_change is not None:
            self._cb_state_change = on_state_change
        if on_session_start is not None:
            self._cb_session_start = on_session_start
        if on_early_warning is not None:
            self._cb_early_warning = on_early_warning
        if on_pause is not None:
            self._cb_pause = on_pause
        if on_resume is not None:
            self._cb_resume = on_resume
        if on_stop is not None:
            self._cb_stop = on_stop

    def _emit(self, attr: str, *args):
        cb = getattr(self, attr, None)
        if cb is None:
            return
        try:
            cb(*args)
        except Exception:
            logger.exception("Event callback %s raised", attr)

    def start_session(
        self, session_type: SessionType, duration_minutes: Optional[int] = None
    ) -> bool:
        if self.state == SessionState.RUNNING:
            logger.warning("start_session called while running — ignored")
            return False

        self.session_type = session_type
        if duration_minutes is None:
            duration_map = {
                SessionType.WORK: self.config.get("work_mins", 25),
                SessionType.SHORT_BREAK: self.config.get("short_break_mins", 5),
                SessionType.LONG_BREAK: self.config.get("long_break_mins", 15),
                SessionType.CUSTOM: 25,
            }
            duration_minutes = duration_map[session_type]

        self.session_duration = int(duration_minutes) * 60
        self.elapsed_seconds = 0
        self.start_time = datetime.now()
        self.pause_time = None

        self._set_state(SessionState.RUNNING)
        self._emit("_cb_session_start", session_type, duration_minutes)

        self._stop_event.clear()
        self._pause_event.set()

        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

        self._start_auto_save()
        self._log_event("Started", duration_minutes)
        logger.info(
            "Session started: %s (%d min)", session_type.value, duration_minutes
        )
        return True

    def pause_session(self) -> bool:
        if self.state != SessionState.RUNNING:
            return False
        self.pause_time = datetime.now()
        self._pause_event.clear()
        self._set_state(SessionState.PAUSED)
        self._emit("_cb_pause", self.session_type)
        logger.info("Session paused at %ds", self.elapsed_seconds)
        return True

    def resume_session(self) -> bool:
        if self.state != SessionState.PAUSED:
            return False
        self.pause_time = None
        self._pause_event.set()
        self._set_state(SessionState.RUNNING)
        self._emit("_cb_resume", self.session_type)
        logger.info("Session resumed")
        return True

    def stop_session(self) -> bool:
        if self.state not in (SessionState.RUNNING, SessionState.PAUSED):
            return False

        self._stop_event.set()
        self._pause_event.set()

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)

        self._stop_auto_save()
        _STATE_FILE.unlink(missing_ok=True)

        elapsed = round(self.elapsed_seconds / 60, 1)
        self._set_state(SessionState.STOPPED)
        self._emit("_cb_stop", self.session_type, elapsed)
        self._log_event("Stopped", elapsed)
        logger.info("Session stopped after %.1f minutes", elapsed)
        return True

    def _timer_loop(self):
        early_warning_secs = self.config.get("notify_early_warning", 2) * 60
        early_warning_sent = False

        while (
            not self._stop_event.is_set()
            and self.elapsed_seconds < self.session_duration
        ):
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            self.elapsed_seconds += 1
            remaining = self.session_duration - self.elapsed_seconds

            if not early_warning_sent and 0 < remaining <= early_warning_secs:
                self._emit(
                    "_cb_early_warning",
                    self.session_type,
                    max(1, round(remaining / 60)),
                )
                early_warning_sent = True

            self._emit("_cb_tick", self.elapsed_seconds, self.session_duration)
            time.sleep(1)

        if (
            not self._stop_event.is_set()
            and self.elapsed_seconds >= self.session_duration
        ):
            self._complete_session()

    def _complete_session(self):
        self._stop_auto_save()
        _STATE_FILE.unlink(missing_ok=True)

        self._set_state(SessionState.COMPLETED)
        duration_minutes = self.session_duration // 60

        self.session_count += 1
        if self.session_type == SessionType.WORK:
            self.completed_work_sessions += 1

        self._log_event("Completed", duration_minutes)
        logger.info("Completed: %s (%d min)", self.session_type.value, duration_minutes)
        self._emit("_cb_complete", self.session_type, duration_minutes)
        self._schedule_next_session()

    def _schedule_next_session(self):
        should_auto, next_type, duration = self._calc_next_session()
        if not should_auto:
            return
        delay = self.config.get("auto_start_delay", 2)

        def _start():
            time.sleep(delay)
            if not self._stop_event.is_set():
                self.start_session(next_type, duration)

        threading.Thread(target=_start, daemon=True).start()

    def _calc_next_session(self):
        if self.session_type == SessionType.WORK:
            long_iv = self.config.get("long_break_interval", 4)
            if self.completed_work_sessions % long_iv == 0:
                return (
                    self.config.get("auto_start_break", True),
                    SessionType.LONG_BREAK,
                    self.config.get("long_break_mins", 15),
                )
            return (
                self.config.get("auto_start_break", True),
                SessionType.SHORT_BREAK,
                self.config.get("short_break_mins", 5),
            )
        # After breaks: short breaks auto-start work, long breaks require manual start
        if self.session_type == SessionType.SHORT_BREAK:
            # Always auto-start work session after short break
            return (
                True,
                SessionType.WORK,
                self.config.get("work_mins", 25),
            )
        elif self.session_type == SessionType.LONG_BREAK:
            # Never auto-start after long break - require manual start
            return (
                False,
                SessionType.WORK,
                self.config.get("work_mins", 25),
            )
        # Default behavior for custom or other types
        return (
            self.config.get("auto_start_work", False),
            SessionType.WORK,
            self.config.get("work_mins", 25),
        )

    def _set_state(self, new_state: SessionState):
        old = self.state
        self.state = new_state
        if old != new_state:
            self._emit("_cb_state_change", old, new_state)

    def _start_auto_save(self):
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            return
        self._auto_save_stop.clear()
        self._auto_save_thread = threading.Thread(
            target=self._auto_save_loop, daemon=True
        )
        self._auto_save_thread.start()

    def _stop_auto_save(self):
        self._auto_save_stop.set()

    def _auto_save_loop(self):
        while not self._auto_save_stop.wait(timeout=_AUTO_SAVE_INTERVAL):
            self._save_state()

    def _save_state(self):
        if self.state not in (SessionState.RUNNING, SessionState.PAUSED):
            return
        snapshot = {
            "session_type": self.session_type.value,
            "session_duration": self.session_duration,
            "elapsed_seconds": self.elapsed_seconds,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completed_work_sessions": self.completed_work_sessions,
            "session_count": self.session_count,
            "saved_at": datetime.now().isoformat(),
        }
        try:
            _STATE_FILE.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        except OSError:
            logger.exception("Failed to write crash-recovery state")

    def load_saved_state(self) -> Optional[Dict]:
        if not _STATE_FILE.exists():
            return None
        try:
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            logger.info(
                "Crash-recovery state found (saved at %s)", data.get("saved_at")
            )
            return data
        except (OSError, json.JSONDecodeError):
            logger.exception("Cannot parse crash-recovery state; discarding")
            _STATE_FILE.unlink(missing_ok=True)
            return None

    def clear_saved_state(self):
        _STATE_FILE.unlink(missing_ok=True)

    def _log_event(self, event: str, duration: float):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (
            f"{ts} - {event} {self.session_type.value} session ({duration} minutes)\n"
        )
        try:
            with open(self.log_file, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            logger.exception("Failed to write session log")

    def log_session(self, session_type: str, duration: int, status: str):
        """Legacy interface used by main.py quick sessions."""
        type_map = {
            "work": SessionType.WORK,
            "short_break": SessionType.SHORT_BREAK,
            "long_break": SessionType.LONG_BREAK,
            "break": SessionType.SHORT_BREAK,
            "custom": SessionType.CUSTOM,
        }
        self.session_type = type_map.get(session_type, SessionType.WORK)
        self._log_event(status.title(), duration)
        if status.lower() == "completed":
            self.session_count += 1
            if self.session_type == SessionType.WORK:
                self.completed_work_sessions += 1

    def get_session_info(self) -> Dict:
        remaining = max(0, self.session_duration - self.elapsed_seconds)
        progress = (
            self.elapsed_seconds / self.session_duration * 100
            if self.session_duration > 0
            else 0.0
        )
        return {
            "type": self.session_type.value,
            "state": self.state.value,
            "duration_total": self.session_duration,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": remaining,
            "progress_percent": min(100.0, max(0.0, progress)),
            "start_time": self.start_time,
            "pause_time": self.pause_time,
            "session_count": self.session_count,
            "completed_work_sessions": self.completed_work_sessions,
        }

    def get_time_display(self, show_seconds: bool = True) -> str:
        remaining = max(0, self.session_duration - self.elapsed_seconds)
        m, s = divmod(remaining, 60)
        return f"{m:02d}:{s:02d}" if show_seconds else f"{m:02d}:00"

    def get_session_statistics(self) -> Dict:
        stats: Dict = {
            "total_sessions": 0,
            "work_sessions": 0,
            "break_sessions": 0,
            "total_work_time": 0.0,
            "total_break_time": 0.0,
            "average_work_session": 0.0,
            "average_break_session": 0.0,
            "today_sessions": 0,
            "today_work_time": 0.0,
        }
        if not self.log_file.exists():
            return stats
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with open(self.log_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    if "Completed" not in line:
                        continue
                    stats["total_sessions"] += 1
                    dur = 0.0
                    if "(" in line and "minutes)" in line:
                        try:
                            dur = float(line.split("(")[1].split(" minutes)")[0])
                        except (ValueError, IndexError):
                            pass
                    if "work session" in line:
                        stats["work_sessions"] += 1
                        stats["total_work_time"] += dur
                        if line.startswith(today):
                            stats["today_sessions"] += 1
                            stats["today_work_time"] += dur
                    elif "break session" in line:
                        stats["break_sessions"] += 1
                        stats["total_break_time"] += dur
                        if line.startswith(today):
                            stats["today_sessions"] += 1
            if stats["work_sessions"]:
                stats["average_work_session"] = (
                    stats["total_work_time"] / stats["work_sessions"]
                )
            if stats["break_sessions"]:
                stats["average_break_session"] = (
                    stats["total_break_time"] / stats["break_sessions"]
                )
        except OSError:
            logger.exception("Error reading session statistics")
        return stats

    def cleanup(self):
        if self.state in (SessionState.RUNNING, SessionState.PAUSED):
            self.stop_session()
        else:
            _STATE_FILE.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# TASK MANAGER
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class Task:
    """Represents a daily task."""

    id: str
    title: str
    google_id: Optional[str] = None
    description: str = ""
    completed: bool = False
    pomodoros_planned: int = 1
    pomodoros_completed: int = 0
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def mark_complete(self):
        self.completed = True
        self.completed_at = datetime.now().isoformat()

    def add_pomodoro(self):
        self.pomodoros_completed += 1

    def remove_pomodoro(self):
        if self.pomodoros_completed > 0:
            self.pomodoros_completed -= 1

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        return cls(**data)


class TaskManager:
    """Manages daily tasks for the focus timer.

    File writes are performed in a background thread to avoid blocking
    the Tkinter main loop.  A threading.Lock serialises concurrent writes.
    """

    def __init__(
        self,
        data_dir: Path = None,
        google_integration: Optional[GoogleIntegration] = None,
        google_task_list_id: Optional[str] = None,
    ):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "daily_tasks.json" if data_dir else TASKS_FILE
        self.tasks: Dict[str, List[Task]] = {}
        self._lock = threading.Lock()
        self._sync_lock = threading.Lock()
        self.google_integration = google_integration
        self.google_task_list_id = google_task_list_id or DEFAULT_TASK_LIST_ID
        self._sync_queue_file = self.data_dir / "sync_queue.json"
        self._sync_queue: List[Dict[str, Any]] = self._load_sync_queue()
        self._sync_states: Dict[str, str] = {}
        self.load_tasks()
        # Try flushing any queued operations on startup without blocking the caller
        if self.google_integration:
            self._process_sync_queue_async()

    def get_today_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def set_google_integration(
        self, integration: Optional[GoogleIntegration], task_list_id: Optional[str] = None
    ) -> None:
        """Attach Google integration after construction."""
        self.google_integration = integration
        if task_list_id:
            self.google_task_list_id = task_list_id
        if self.google_integration:
            self._process_sync_queue_async()

    def _can_sync(self) -> bool:
        return bool(
            self.google_integration
            and getattr(self.google_integration, "is_enabled", lambda: False)()
        )

    def _load_sync_queue(self) -> List[Dict[str, Any]]:
        if not self.data_dir.exists():
            return []
        try:
            if self._sync_queue_file.exists():
                with open(self._sync_queue_file, "r", encoding="utf-8") as fh:
                    return json.load(fh)
        except Exception:
            logger.exception("Error loading sync queue")
        return []

    def _save_sync_queue(self) -> None:
        try:
            with open(self._sync_queue_file, "w", encoding="utf-8") as fh:
                json.dump(self._sync_queue, fh, indent=2, ensure_ascii=False)
        except OSError:
            logger.exception("Error saving sync queue")

    def _process_sync_queue_async(self, force: bool = False) -> None:
        threading.Thread(
            target=self._process_sync_queue, args=(force,), daemon=True
        ).start()

    def _process_sync_queue(self, force: bool = False) -> None:
        if not self._can_sync():
            return
        now = time.time()
        with self._sync_lock:
            remaining: List[Dict[str, Any]] = []
            for entry in list(self._sync_queue):
                next_attempt = entry.get("next_attempt", 0)
                if not force and next_attempt > now:
                    remaining.append(entry)
                    continue
                success = self._perform_sync_action(entry)
                if success:
                    continue
                entry["retries"] = entry.get("retries", 0) + 1
                delay = min(900, 5 * (2 ** (entry["retries"] - 1)))
                entry["next_attempt"] = now + delay
                remaining.append(entry)
            self._sync_queue = remaining
            self._save_sync_queue()

    def _enqueue_sync(self, action: str, task: Task) -> None:
        payload = task.to_dict()
        entry = {
            "action": action,
            "task_id": task.id,
            "google_id": task.google_id,
            "payload": payload,
            "retries": 0,
            "next_attempt": time.time(),
        }
        with self._sync_lock:
            self._sync_states[task.id] = "pending"
            self._sync_queue.append(entry)
            self._save_sync_queue()

    def _perform_sync_action(self, entry: Dict[str, Any]) -> bool:
        if not self._can_sync():
            return False
        action = entry.get("action")
        payload: Dict[str, Any] = entry.get("payload", {})
        task_id = entry.get("task_id")
        task = self.get_task_by_id(task_id) if task_id else None
        google_id = (task.google_id if task else None) or entry.get("google_id")
        try:
            if action == "create":
                result = self.google_integration.create_task(
                    self.google_task_list_id,
                    payload.get("title", ""),
                    payload.get("description", ""),
                )
                if result and result.get("id"):
                    google_id = result["id"]
                    if task:
                        task.google_id = google_id
                        self.save_tasks()
                    self._sync_states[task_id] = "synced"
                    return True
                return False
            if action == "update":
                if not google_id:
                    return self._perform_sync_action({**entry, "action": "create"})
                result = self.google_integration.update_task(
                    self.google_task_list_id,
                    google_id,
                    title=payload.get("title") or (task.title if task else None),
                    notes=payload.get("description") or (task.description if task else None),
                    completed=payload.get("completed")
                    if payload.get("completed") is not None
                    else (task.completed if task else None),
                )
                if result is not None:
                    self._sync_states[task_id] = "synced"
                    return True
                return False
            if action == "delete":
                if not google_id:
                    return True
                success = self.google_integration.delete_task(
                    self.google_task_list_id, google_id
                )
                if success and task_id:
                    self._sync_states[task_id] = "synced"
                return success
        except Exception as exc:
            logger.warning("Sync action %s failed for %s: %s", action, task_id, exc)
            entry["last_error"] = str(exc)
            self._sync_states[task_id] = "error"
            return False
        return False

    def _sync_new_task(self, task: Task) -> None:
        if not self.google_integration:
            return

        def _worker():
            if not self._can_sync():
                self._enqueue_sync("create", task)
                return
            try:
                result = self.google_integration.create_task(
                    self.google_task_list_id, task.title, task.description
                )
                if result and result.get("id"):
                    task.google_id = result["id"]
                    self._sync_states[task.id] = "synced"
                    self.save_tasks()
                else:
                    self._enqueue_sync("create", task)
            except Exception:
                self._enqueue_sync("create", task)

        threading.Thread(target=_worker, daemon=True).start()

    def _sync_task_update(self, task: Task) -> None:
        if not self.google_integration:
            return

        def _worker():
            if not self._can_sync():
                self._enqueue_sync("update", task)
                return
            try:
                if not task.google_id:
                    self._enqueue_sync("create", task)
                    return
                result = self.google_integration.update_task(
                    self.google_task_list_id,
                    task.google_id,
                    title=task.title,
                    notes=task.description,
                    completed=task.completed,
                )
                if result is None:
                    self._enqueue_sync("update", task)
                else:
                    self._sync_states[task.id] = "synced"
            except Exception:
                self._enqueue_sync("update", task)

        threading.Thread(target=_worker, daemon=True).start()

    def _sync_task_delete(self, task: Task) -> None:
        if not self.google_integration:
            return

        def _worker():
            if not self._can_sync():
                if task.google_id:
                    self._enqueue_sync("delete", task)
                return
            if not task.google_id:
                return
            success = self.google_integration.delete_task(
                self.google_task_list_id, task.google_id
            )
            if not success:
                self._enqueue_sync("delete", task)

        threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            if value.endswith("Z"):
                value = value.replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except Exception:
            return None

    def _remote_task_matches_today(self, remote_task: Dict[str, Any], today_key: str) -> bool:
        """Filter remote tasks to only those updated or due today."""
        for key in ("due", "updated", "completed"):
            ts = self._parse_timestamp(remote_task.get(key))
            if ts and ts.strftime("%Y-%m-%d") == today_key:
                return True
        return False

    def sync_with_cloud(self) -> Dict[str, int]:
        """Bidirectional sync between local tasks and Google Tasks."""
        summary = {"pushed": 0, "pulled": 0, "updated": 0, "queued": 0}
        if not self._can_sync():
            summary["queued"] = len(self._sync_queue)
            return summary

        self._process_sync_queue(force=True)

        today_key = self.get_today_key()
        local_tasks = list(self.tasks.get(today_key, []))
        try:
            remote_tasks = self.google_integration.fetch_remote_tasks(
                self.google_task_list_id, include_completed=True
            )
        except Exception as exc:
            logger.warning("Failed to fetch remote tasks: %s", exc)
            return summary

        remote_by_id = {t.get("id"): t for t in remote_tasks if t.get("id")}
        local_by_gid = {t.google_id: t for t in local_tasks if t.google_id}

        # Push local tasks that are missing a google_id
        for task in local_tasks:
            if task.google_id:
                continue
            try:
                created = self.google_integration.create_task(
                    self.google_task_list_id, task.title, task.description
                )
                if created and created.get("id"):
                    task.google_id = created["id"]
                    summary["pushed"] += 1
                else:
                    self._enqueue_sync("create", task)
                    summary["queued"] += 1
            except Exception as exc:
                logger.debug("Queueing task %s for later sync: %s", task.id, exc)
                self._enqueue_sync("create", task)
                summary["queued"] += 1

        # Pull remote tasks not present locally (for today only)
        for remote_id, remote_task in remote_by_id.items():
            if remote_id in local_by_gid:
                continue
            if not self._remote_task_matches_today(remote_task, today_key):
                continue
            task = Task(
                id=f"{today_key}_{remote_id}",
                title=remote_task.get("title", "Untitled Task"),
                description=remote_task.get("notes", ""),
                completed=remote_task.get("status") == "completed",
                pomodoros_planned=1,
                pomodoros_completed=0,
                created_at=remote_task.get("updated", datetime.now().isoformat()),
                completed_at=remote_task.get("completed"),
                google_id=remote_id,
            )
            self.tasks.setdefault(today_key, []).append(task)
            summary["pulled"] += 1

        # Resolve conflicts based on completed_at recency
        for google_id, task in local_by_gid.items():
            remote_task = remote_by_id.get(google_id)
            if not remote_task:
                continue
            remote_completed = self._parse_timestamp(remote_task.get("completed"))
            local_completed = self._parse_timestamp(task.completed_at)
            if remote_completed and (
                not local_completed or remote_completed > local_completed
            ):
                task.completed = True
                task.completed_at = remote_task.get("completed")
                summary["updated"] += 1
            elif local_completed and (
                not remote_completed or local_completed > remote_completed
            ):
                try:
                    updated = self.google_integration.update_task(
                        self.google_task_list_id,
                        google_id,
                        title=task.title,
                        notes=task.description,
                        completed=task.completed,
                    )
                    if updated is None:
                        self._enqueue_sync("update", task)
                        summary["queued"] += 1
                    else:
                        summary["updated"] += 1
                except Exception:
                    self._enqueue_sync("update", task)
                    summary["queued"] += 1

        self.save_tasks()
        return summary

    def get_sync_status(self, task_id: str) -> str:
        """Return sync status for UI indicator."""
        if any(entry.get("task_id") == task_id for entry in self._sync_queue):
            return "pending"
        if self._sync_states.get(task_id) == "error":
            return "error"
        if not self.google_integration or not self.google_integration.is_enabled():
            return "disabled"
        task = self.get_task_by_id(task_id)
        if task and task.google_id:
            return "synced"
        return "local"

    def load_tasks(self):
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for date_key, task_list in data.items():
                    self.tasks[date_key] = [Task.from_dict(td) for td in task_list]
            except (json.JSONDecodeError, Exception):
                logger.exception("Error loading tasks from %s", self.tasks_file)
                self.tasks = {}

    def save_tasks(self):
        with self._lock:
            data = {
                date_key: [t.to_dict() for t in task_list]
                for date_key, task_list in self.tasks.items()
            }
        threading.Thread(target=self._write_tasks, args=(data,), daemon=True).start()

    def _write_tasks(self, data: dict):
        with self._lock:
            try:
                with open(self.tasks_file, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
            except OSError:
                logger.exception("Error saving tasks to %s", self.tasks_file)

    def get_today_tasks(self) -> List[Task]:
        return self.tasks.get(self.get_today_key(), [])

    def add_task(
        self, title: str, description: str = "", pomodoros_planned: int = 1
    ) -> Task:
        today_key = self.get_today_key()
        task_id = f"{today_key}_{datetime.now().strftime('%H%M%S%f')}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            pomodoros_planned=pomodoros_planned,
        )
        if today_key not in self.tasks:
            self.tasks[today_key] = []
        self.tasks[today_key].insert(0, task)
        self.save_tasks()
        self._sync_new_task(task)
        return task

    def complete_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task:
            task.mark_complete()
            self.save_tasks()
            self._sync_task_update(task)
            return True
        return False

    def toggle_task_completion(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task:
            if task.completed:
                task.completed = False
                task.completed_at = None
            else:
                task.mark_complete()
            self.save_tasks()
            self._sync_task_update(task)
            return True
        return False

    def add_pomodoro_to_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task:
            task.add_pomodoro()
            self.save_tasks()
            return True
        return False

    def remove_pomodoro_from_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task and task.pomodoros_completed > 0:
            task.remove_pomodoro()
            self.save_tasks()
            return True
        return False

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        for task in self.get_today_tasks():
            if task.id == task_id:
                return task
        return None

    def delete_task(self, task_id: str) -> bool:
        today_key = self.get_today_key()
        if today_key not in self.tasks:
            return False
        task = self.get_task_by_id(task_id)
        if task:
            self._sync_task_delete(task)
        self.tasks[today_key] = [t for t in self.tasks[today_key] if t.id != task_id]
        self.save_tasks()
        return True

    def reorder_tasks(self, task_id: str, dest_index: int) -> bool:
        """Move task with task_id to dest_index position in today's list."""
        today_key = self.get_today_key()
        if today_key not in self.tasks:
            return False
        task_list = self.tasks[today_key]
        src_index = next((i for i, t in enumerate(task_list) if t.id == task_id), -1)
        if src_index < 0:
            return False
        dest_index = max(0, min(dest_index, len(task_list) - 1))
        task = task_list.pop(src_index)
        task_list.insert(dest_index, task)
        self.save_tasks()
        return True

    def update_task_title(self, task_id: str, new_title: str) -> bool:
        task = self.get_task_by_id(task_id)
        if task:
            task.title = new_title
            self.save_tasks()
            self._sync_task_update(task)
            return True
        return False

    def get_incomplete_tasks(self) -> List[Task]:
        return [t for t in self.get_today_tasks() if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        return [t for t in self.get_today_tasks() if t.completed]

    def get_task_stats(self) -> Dict:
        tasks = self.get_today_tasks()
        if not tasks:
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "completion_rate": 0,
                "total_pomodoros_planned": 0,
                "total_pomodoros_completed": 0,
            }
        completed = len(self.get_completed_tasks())
        total = len(tasks)
        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "total_pomodoros_planned": sum(t.pomodoros_planned for t in tasks),
            "total_pomodoros_completed": sum(t.pomodoros_completed for t in tasks),
        }

    def has_tasks_for_today(self) -> bool:
        return len(self.get_today_tasks()) > 0

    def cleanup_old_tasks(self, days_to_keep: int = 30):
        try:
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            keys_to_remove = [key for key in self.tasks if key < cutoff_str]
            for key in keys_to_remove:
                del self.tasks[key]
            if keys_to_remove:
                logger.info(
                    "Removed %d old task day(s) before %s",
                    len(keys_to_remove),
                    cutoff_str,
                )
                self.save_tasks()
        except Exception:
            logger.exception("Error cleaning up old tasks")
