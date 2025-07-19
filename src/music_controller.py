#!/usr/bin/env python3
"""
Cross-Platform Music Controller for Enhanced Focus Timer
Manages classical music playback using MPV player
"""

import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class MusicController:
    """Cross-platform music controller using MPV"""

    def __init__(self, config_manager):
        """Initialize music controller with configuration"""
        self.config = config_manager
        self.mpv_process = None
        self.pid_file = Path("mpv_classical.pid")

        # Platform-specific MPV executable detection
        self.mpv_executable = self._find_mpv_executable()

        # Current playlist info
        self.current_playlist = None
        self.is_playing = False

    def _find_mpv_executable(self) -> str:
        """Find MPV executable based on platform"""
        mpv_path = self.config.get("mpv_executable", "mpv")

        # Try configured path first
        if self._test_mpv_executable(mpv_path):
            return mpv_path

        # If running as PyInstaller executable, check the executable directory
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).parent
            exe_mpv_paths = [
                exe_dir / "mpv.exe",
                exe_dir / "mpv",
                exe_dir / "_internal" / "mpv.exe",
                exe_dir / "_internal" / "mpv",
            ]
            for path in exe_mpv_paths:
                if self._test_mpv_executable(str(path)):
                    return str(path)

        # Platform-specific search paths
        if platform.system() == "Darwin":  # macOS
            mac_paths = [
                "/usr/local/bin/mpv",
                "/opt/homebrew/bin/mpv",
                "/usr/bin/mpv",
                "mpv",
            ]
            for path in mac_paths:
                if self._test_mpv_executable(path):
                    return path

        elif platform.system() == "Linux":
            linux_paths = ["/usr/bin/mpv", "/usr/local/bin/mpv", "/snap/bin/mpv", "mpv"]
            for path in linux_paths:
                if self._test_mpv_executable(path):
                    return path

        elif platform.system() == "Windows":
            # Windows paths
            windows_paths = [
                "mpv.exe",
                "mpv",
                str(Path.home() / "AppData" / "Local" / "mpv" / "mpv.exe"),
                "C:/Program Files/mpv/mpv.exe",
                "C:/Program Files (x86)/mpv/mpv.exe",
            ]
            for path in windows_paths:
                if self._test_mpv_executable(path):
                    return path

        # Default fallback
        return "mpv"

    def _test_mpv_executable(self, path: str) -> bool:
        """Test if MPV executable is working"""
        try:
            result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (
            subprocess.SubprocessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            return False

    def is_mpv_available(self) -> bool:
        """Check if MPV is available and working"""
        return self._test_mpv_executable(self.mpv_executable)

    def get_available_playlists(self) -> List[Dict[str, Any]]:
        """Get list of available playlists"""
        return self.config.get_music_playlists()

    def _select_default_playlist(self) -> Optional[str]:
        """Select the default playlist to use"""
        playlists = self.get_available_playlists()

        if not playlists:
            print("No playlists available")
            return None

        # Check if user has selected a specific playlist
        selected_playlist = self.config.get("classical_music_default_playlist")
        if selected_playlist:
            # Verify the selected playlist still exists
            for playlist in playlists:
                if (
                    playlist["path"] == selected_playlist
                    or playlist["name"] == selected_playlist
                ):
                    return playlist["path"]
            print(f"Selected playlist '{selected_playlist}' not found, using default")

        # Prefer local playlists if in local mode
        if self.config.get("classical_music_local_mode"):
            local_playlists = [p for p in playlists if p["type"] == "local"]
            if local_playlists:
                return local_playlists[0]["path"]

        # Use first available playlist
        return playlists[0]["path"]

    def start_music(
        self, playlist_path: Optional[str] = None, volume: Optional[int] = None
    ) -> bool:
        """Start classical music playback"""
        if not self.is_mpv_available():
            print("MPV is not available. Please install MPV for music support.")
            return False

        # Stop any existing playback
        self.stop_music()

        # Select playlist
        if not playlist_path:
            playlist_path = self._select_default_playlist()

        if not playlist_path:
            print("❌ No playlist available to play")
            return False

        # Set volume
        if volume is None:
            volume = self.config.get("classical_music_volume", 30)

        

        # Build MPV arguments
        mpv_args = [
            self.mpv_executable,
            "--no-video",
            "--shuffle",
            "--loop-playlist",
            f"--volume={volume}",
            "--really-quiet",
        ]

        # Add extra arguments from config
        extra_args = self.config.get("mpv_extra_args", "")
        if extra_args:
            mpv_args.extend(extra_args.split())

        # Add playlist
        if playlist_path:
            mpv_args.append(playlist_path)
        else:
            print("No valid playlist path to play")
            return False

        try:
            # Start MPV process
            self.mpv_process = subprocess.Popen(
                mpv_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

            # Save PID for process management
            with open(self.pid_file, "w") as f:
                f.write(str(self.mpv_process.pid))

            self.current_playlist = playlist_path
            self.is_playing = True

            return True

        except Exception as e:
            print(f"Error starting MPV: {e}")
            return False

    def stop_music(self) -> bool:
        """Stop classical music playback"""
        stopped = False

        # Stop current process
        if self.mpv_process and self.mpv_process.poll() is None:
            try:
                if platform.system() == "Windows":
                    self.mpv_process.terminate()
                else:
                    self.mpv_process.send_signal(signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self.mpv_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.mpv_process.kill()

                stopped = True
            except Exception as e:
                print(f"Error stopping music process: {e}")

        # Also try to stop by PID file
        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())

                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)], capture_output=True
                    )
                else:
                    os.kill(pid, signal.SIGTERM)

                self.pid_file.unlink()
                if not stopped:
                    stopped = True

            except (FileNotFoundError, ProcessLookupError, ValueError):
                pass
            except Exception as e:
                print(f"Error stopping music by PID: {e}")

        # Reset state
        self.mpv_process = None
        self.current_playlist = None
        self.is_playing = False

        return True

    def set_volume(self, volume: int) -> bool:
        """Set music volume (0-100)"""
        if not self.is_playing:
            print("No music currently playing")
            return False

        # For basic implementation, we'll restart with new volume
        # Advanced MPV control would require IPC/JSON API
        print(f"Setting volume to {volume}%")
        print("Note: Volume will take effect on next music start")

        # Update config for next session
        self.config.set("classical_music_volume", volume)

        return True

    def pause_music(self) -> bool:
        """Pause music playback"""
        if not self.is_playing:
            return False

        # For simplicity, we'll stop the music
        # Advanced implementation would use MPV IPC for true pause/resume
        return self.stop_music()

    def resume_music(self) -> bool:
        """Resume music playback"""
        if self.is_playing:
            return False

        return self.start_music(self.current_playlist)

    def get_status(self) -> Dict[str, Any]:
        """Get current music status"""
        return {
            "is_playing": self.is_playing,
            "current_playlist": self.current_playlist,
            "mpv_available": self.is_mpv_available(),
            "volume": self.config.get("classical_music_volume", 30),
        }

    def test_mpv(self) -> bool:
        """Test MPV installation and functionality"""
        print("🧪 Testing MPV installation...")

        if not self.is_mpv_available():
            print("MPV is not installed or not accessible")
            print("Please install MPV:")
            print("Windows: choco install mpv  or  winget install mpv")
            print("macOS: brew install mpv")
            print("Linux: sudo apt install mpv  or  sudo yum install mpv")
            print("Or download from: https://mpv.io/")
            return False

        try:
            result = subprocess.run(
                [self.mpv_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                print(f"MPV is available: {version_line}")

                # Test with a short audio if available
                playlists = self.get_available_playlists()
                if playlists:
                    print(f"Found {len(playlists)} playlist(s):")
                    for playlist in playlists[:3]:  # Show first 3
                        print(f"   • {playlist['name']} ({playlist['type']})")
                else:
                    print("No playlists configured")

                return True
            else:
                print(f"MPV test failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(" MPV test timed out")
            return False
        except Exception as e:
            print(f"MPV test error: {e}")
            return False

    def cleanup(self):
        """Cleanup resources on exit"""
        self.stop_music()


if __name__ == "__main__":
    # Test music controller functionality
    from config_manager import ConfigManager

    config = ConfigManager()
    music = MusicController(config)

    print("Testing Music Controller...")
    print("=" * 50)

    # Test MPV availability
    music.test_mpv()

    # Show available playlists
    playlists = music.get_available_playlists()
    print(f"\nAvailable playlists: {len(playlists)}")
    for i, playlist in enumerate(playlists, 1):
        print(f"{i}. {playlist['name']} ({playlist['type']})")

    # Test start/stop if user wants
    if playlists:
        test_playback = (
            input("\nTest music playback for 5 seconds? (y/n): ").lower().strip()
        )
        if test_playback == "y":
            print("\nStarting test music...")
            if music.start_music(volume=20):
                time.sleep(5)
                print("Stopping test music...")
                music.stop_music()
            else:
                print("Failed to start test music")

    print("\nMusic controller test complete.")
