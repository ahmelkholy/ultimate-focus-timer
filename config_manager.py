#!/usr/bin/env python3
"""
Configuration Manager for Enhanced Focus Timer
Handles YAML configuration loading and validation
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Manages application configuration from YAML file"""

    DEFAULT_CONFIG = {
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
        "time_format": "15:04",
        "show_progress_bar": True,
        # Sound Settings
        "sound": "",
        "sound_volume": 100,
        "sound_on_break": False,
        "fade_sound": True,
        # Classical Music Settings
        "classical_music": True,
        "classical_music_volume": 30,
        "classical_music_local_mode": True,
        "classical_music_default_playlist": "",
        "classical_music_playlist_dir": "",
        "classical_music_online_playlists": [
            "https://www.youtube.com/playlist?list=PLRBp0Fe2GpgmgL97AviPkenNzgzHByGgs",
            "https://www.youtube.com/playlist?list=PLcNiN7SthNjHqrGWzTsJq1OAZ8TUQgOfO",
            "https://www.youtube.com/playlist?list=PLTKWrxUB7R8SYCcrfHONp9QbdA3-CKx6p",
        ],
        "mpv_executable": "mpv",
        "mpv_extra_args": "--no-video --shuffle --loop-playlist",
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
    }

    def __init__(self, config_path: str = "config.yml"):
        """Initialize config manager with path to config file"""
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"Config file not found: {self.config_path}")
            print("Using default configuration")
            return self.config

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f) or {}

            # Merge with defaults
            self.config.update(file_config)

            # Cross-platform path handling
            self._fix_paths()

            print(f"✓ Configuration loaded from {self.config_path}")
            return self.config

        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            print("Using default configuration")
            return self.config

        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return self.config

    def _fix_paths(self):
        """Fix Windows paths for cross-platform compatibility"""
        path_keys = [
            "classical_music_default_playlist",
            "classical_music_playlist_dir",
            "task_file",
            "custom_css",
        ]

        for key in path_keys:
            if key in self.config and self.config[key]:
                # Convert Windows paths to cross-platform
                path = self.config[key]
                if sys.platform != "win32":
                    # Convert Windows-style paths for Unix systems
                    if "\\" in path and ":" in path:
                        # This looks like a Windows absolute path
                        # Remove drive letter and convert separators
                        path = path.split(":", 1)[1] if ":" in path else path
                        path = path.replace("\\", "/")
                        # Map to user home for cross-platform compatibility
                        if path.startswith("/Users/"):
                            path = path.replace("/Users/", "~/")

                self.config[key] = path

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value

    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=True)
            print(f"✓ Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def validate_config(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []

        # Check required numeric values
        numeric_keys = [
            "work_mins",
            "short_break_mins",
            "long_break_mins",
            "classical_music_volume",
        ]
        for key in numeric_keys:
            if (
                not isinstance(self.config.get(key), (int, float))
                or self.config.get(key) < 0
            ):
                issues.append(f"Invalid {key}: must be a positive number")

        # Check volume ranges
        if not 0 <= self.config.get("classical_music_volume", 30) <= 100:
            issues.append("classical_music_volume must be between 0 and 100")

        # Check playlist file exists if specified
        playlist_path = self.config.get("classical_music_default_playlist")
        if playlist_path and not Path(playlist_path).exists():
            issues.append(f"Default playlist not found: {playlist_path}")

        return issues

    def get_music_playlists(self) -> list:
        """Get available music playlists"""
        playlists = []

        # Add default playlist
        default_playlist = self.get("classical_music_default_playlist")
        if default_playlist and Path(default_playlist).exists():
            playlists.append(
                {
                    "name": "Default Classical Music",
                    "path": default_playlist,
                    "type": "local",
                }
            )

        # Add playlists from directory
        playlist_dir = self.get("classical_music_playlist_dir")
        if playlist_dir and Path(playlist_dir).exists():
            for playlist_file in Path(playlist_dir).glob("*.m3u*"):
                playlists.append(
                    {
                        "name": playlist_file.stem,
                        "path": str(playlist_file),
                        "type": "local",
                    }
                )

        # Add online playlists if local mode is disabled
        if not self.get("classical_music_local_mode"):
            online_playlists = self.get("classical_music_online_playlists", [])
            for i, url in enumerate(online_playlists):
                playlists.append(
                    {"name": f"Online Playlist {i + 1}", "path": url, "type": "online"}
                )

        return playlists

    def get_timer_config(self) -> Dict[str, Any]:
        """Get timer-related configuration"""
        return {
            "work_duration": self.get("work_mins", 25),
            "short_break_duration": self.get("short_break_mins", 5),
            "long_break_duration": self.get("long_break_mins", 15),
            "sessions_until_long_break": self.get("long_break_interval", 4),
            "auto_start_breaks": self.get("auto_start_break", True),
            "auto_start_work": self.get("auto_start_work", False),
            "min_work_time": self.get("min_work_time", 5),
            "max_daily_sessions": self.get("max_daily_sessions", 0),
        }

    def update_timer_config(self, timer_config: Dict[str, Any]) -> None:
        """Update timer configuration"""
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

    def get_music_config(self) -> Dict[str, Any]:
        """Get music-related configuration"""
        return {
            "enabled": self.get("classical_music", True),
            "volume": self.get("classical_music_volume", 30),
            "shuffle": self.get("classical_music_shuffle", True),
            "repeat": self.get("classical_music_repeat", True),
            "local_mode": self.get("classical_music_local_mode", False),
            "pause_on_break": self.get("pause_music_on_break", True),
            "mpv_path": self.get("mpv_executable", "auto"),
        }

    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification-related configuration"""
        return {
            "enabled": self.get("notify", True),
            "sound": self.get("notify_sound", True),
            "desktop": self.get("desktop_notifications", True),
            "early_warning": self.get("notify_early_warning", 2),
            "priority": self.get("notification_priority", "normal"),
            "persistence": self.get("notification_persistence", 5),
            "motivational": self.get("motivational_messages", True),
        }

    def get_app_config(self) -> Dict[str, Any]:
        """Get application-related configuration"""
        return {
            "theme": self.get("color_scheme", "dark"),
            "accent_color": self.get("accent_color", "#00ff00"),
            "data_path": self.get("log_file", "log/focus.log"),
            "export_path": self.get("export_path", "exports/"),
            "animated_transitions": self.get("animated_transitions", True),
            "productivity_scoring": self.get("productivity_scoring", True),
        }

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"ConfigManager(path={self.config_path}, keys={len(self.config)})"


# Convenience function for global config access
_global_config = None


def get_config(config_path: str = "config.yml") -> ConfigManager:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager(config_path)
    return _global_config


if __name__ == "__main__":
    # Test configuration loading
    config = ConfigManager()
    print(f"Loaded configuration: {config}")
    print(f"Work session duration: {config.get('work_mins')} minutes")
    print(f"Classical music enabled: {config.get('classical_music')}")

    issues = config.validate_config()
    if issues:
        print("Configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Configuration is valid")

    playlists = config.get_music_playlists()
    print(f"Available playlists: {len(playlists)}")
    for playlist in playlists:
        print(f"  - {playlist['name']} ({playlist['type']})")
        print(f"  - {playlist['name']} ({playlist['type']})")
