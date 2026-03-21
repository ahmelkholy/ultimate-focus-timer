#!/usr/bin/env python3
"""
Configuration Manager for Ultimate Focus Timer.

Loads config.yml and exposes typed dataclasses for each config domain.
Raw dict access via .get() is preserved for backward compatibility.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .app_paths import CONFIG_FILE

logger = logging.getLogger(__name__)


# ── Typed config dataclasses ───────────────────────────────────────────────────


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


# ── ConfigManager ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    # Session Timings
    "work_mins": 25,
    "short_break_mins": 5,
    "long_break_mins": 15,
    "long_break_interval": 4,
    # Session Messages
    "work_msg": "Focus on your task",
    "short_break_msg": "Take a breather",
    "long_break_msg": "Take a long break",
    # Notification Settings
    "notify": True,
    "notify_sound": True,
    "notify_early_warning": 2,
    "desktop_notifications": True,
    "notification_priority": "normal",
    "motivational_messages": True,
    "notification_persistence": 5,
    # Session Behavior
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
    # Time Display
    "24hr_clock": False,
    "show_seconds": True,
    "show_progress_bar": True,
    # Sound Settings
    "sound": "",
    "sound_volume": 100,
    "sound_on_break": False,
    "fade_sound": True,
    # Classical Music Settings
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
    # NOTE: extra args are handled in code; duplicates are avoided at launch time
    "mpv_extra_args": "",
    "fade_music_transitions": True,
    "pause_music_on_break": True,
    "classical_music_genres": ["baroque", "classical", "romantic", "modern"],
    # Theme Settings
    "dark_theme": True,
    "accent_color": "#00ff00",
    "compact_mode": False,
    "animated_transitions": True,
    "gradient_backgrounds": True,
    "transparency": 0.95,
    "blur_background": True,
    "color_scheme": "forest",
    "custom_css": "",
    # Statistics
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
    # Task Management
    "todo_integration": False,
    "task_file": "~/tasks.md",
    "auto_task_complete": True,
    # Window
    "window_geometry": "",
}


class ConfigManager:
    """Loads application configuration from YAML and provides typed accessors."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path: Path = config_path or CONFIG_FILE
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load()

    # ── Internal loading ───────────────────────────────────────────────────────

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

    def _normalise_paths(self) -> None:
        """Expand ~ and make playlist paths absolute where possible."""
        path_keys = [
            "classical_music_default_playlist",
            "classical_music_selected_playlist",
            "classical_music_playlist_dir",
            "task_file",
        ]
        for key in path_keys:
            raw = self.config.get(key)
            if raw:
                expanded = str(Path(raw).expanduser())
                self.config[key] = expanded

    # ── Raw dict access (backward compat) ─────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value

    # ── Persistence ────────────────────────────────────────────────────────────

    def save_config(self) -> bool:
        try:
            with open(self.config_path, "w", encoding="utf-8") as fh:
                yaml.dump(self.config, fh, default_flow_style=False, sort_keys=True)
            logger.debug("Configuration saved to %s", self.config_path)
            return True
        except OSError as exc:
            logger.error("Error saving config: %s", exc)
            return False

    # ── Typed accessors ────────────────────────────────────────────────────────

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
            # mpv_extra_args is intentionally left empty in default;
            # core flags are hardcoded in MusicController to avoid duplication.
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

    # ── Playlist helpers ───────────────────────────────────────────────────────

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

    # ── Validation ─────────────────────────────────────────────────────────────

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

    # ── Timer config updater (keeps backward compat) ──────────────────────────

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


# ── Legacy singleton (still available but discouraged) ─────────────────────────
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config
