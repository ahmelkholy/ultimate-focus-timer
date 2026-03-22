#!/usr/bin/env python3
"""
Cross-Platform Music Controller for Ultimate Focus Timer.

Manages classical music playback via MPV subprocess.
Bug fixes vs. original:
  - PID file anchored to project root (not CWD)
  - Duplicate MPV args eliminated
  - pause_music preserves playlist so resume_music can restart correctly
"""

import logging
import os
import platform
import signal
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .app_paths import MPV_PID_FILE

logger = logging.getLogger(__name__)


class MusicController:
    """Cross-platform music controller using MPV."""

    def __init__(self, config_manager):
        self.config = config_manager
        self.mpv_process: Optional[subprocess.Popen] = None
        self.pid_file: Path = MPV_PID_FILE

        self.mpv_executable: str = self._find_mpv_executable()
        self._mpv_available: bool = self._test_mpv_executable(self.mpv_executable)
        self.current_playlist: Optional[str] = None
        self._paused_playlist: Optional[str] = None  # saved across pause/stop
        self.is_playing: bool = False

        logger.debug("MusicController ready (mpv=%s)", self.mpv_executable)

    # ── MPV discovery ─────────────────────────────────────────────────────────

    def _find_mpv_executable(self) -> str:
        configured = self.config.get("mpv_executable", "mpv")
        if self._test_mpv_executable(configured):
            return configured

        import sys

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
            search_paths = [
                "/opt/homebrew/bin/mpv",
                "/usr/local/bin/mpv",
                "/usr/bin/mpv",
                "mpv",
            ]
        elif system == "Linux":
            search_paths = [
                "/usr/bin/mpv",
                "/usr/local/bin/mpv",
                "/snap/bin/mpv",
                "mpv",
            ]
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
            result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def is_mpv_available(self) -> bool:
        return self._mpv_available

    # ── Playlist selection ────────────────────────────────────────────────────

    def get_available_playlists(self) -> List[Dict[str, Any]]:
        return self.config.get_music_playlists()

    def _select_default_playlist(self) -> Optional[str]:
        playlists = self.get_available_playlists()
        if not playlists:
            logger.warning("No playlists available")
            return None

        # Prefer the configured default/selected playlist
        for key in (
            "classical_music_selected_playlist",
            "classical_music_default_playlist",
        ):
            configured = self.config.get(key, "")
            if configured:
                for pl in playlists:
                    if pl["path"] == configured or pl["name"] == configured:
                        return pl["path"]

        # Prefer local playlists in local mode
        if self.config.get("classical_music_local_mode", True):
            local = [p for p in playlists if p["type"] == "local"]
            if local:
                return local[0]["path"]

        return playlists[0]["path"]

    # ── Playback ──────────────────────────────────────────────────────────────

    def start_music(
        self, playlist_path: Optional[str] = None, volume: Optional[int] = None
    ) -> bool:
        if not self.is_mpv_available():
            logger.warning("MPV not available; skipping music start")
            return False

        # Stop cleanly before (re)starting, but preserve playlist context
        self._stop_process_only()

        if not playlist_path:
            playlist_path = self._paused_playlist or self._select_default_playlist()

        if not playlist_path:
            logger.error("No playlist available to play")
            return False

        if volume is None:
            volume = int(self.config.get("classical_music_volume", 30))

        # Build args — core flags hardcoded once, extra_args from config appended
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
            )
            self.pid_file.write_text(str(self.mpv_process.pid))
            self.current_playlist = playlist_path
            self._paused_playlist = playlist_path
            self.is_playing = True
            logger.info(
                "Music started (pid=%d, playlist=%s)",
                self.mpv_process.pid,
                playlist_path,
            )
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
        """Terminate the MPV process but don't reset playlist tracking."""
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
                        ["taskkill", "/F", "/PID", str(pid)], capture_output=True
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
        """Pause playback — saves the current playlist so resume can restart it."""
        if not self.is_playing:
            return False
        self._paused_playlist = self.current_playlist  # preserve before stop clears it
        self._stop_process_only()
        self.current_playlist = None
        self.is_playing = False
        logger.info("Music paused (saved playlist: %s)", self._paused_playlist)
        return True

    def resume_music(self) -> bool:
        """Resume from the playlist that was playing before pause."""
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
