#!/usr/bin/env python3
"""
Daemon Manager - Start/stop HTTP daemon from GUI
"""

import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from .system import PROJECT_ROOT

logger = logging.getLogger(__name__)


class DaemonManager:
    """Manages the HTTP daemon lifecycle"""

    DAEMON_PID_FILE = PROJECT_ROOT / "daemon.pid"
    DAEMON_PORT = 8765
    DAEMON_HOST = "127.0.0.1"

    def __init__(self, on_status_changed: Optional[Callable[[str], None]] = None):
        """
        Initialize daemon manager

        Args:
            on_status_changed: Callback when daemon status changes (status: str)
        """
        self.on_status_changed = on_status_changed
        self._daemon_process: Optional[subprocess.Popen] = None
        self._status = "unknown"  # unknown, stopped, running, error
        self._check_thread: Optional[threading.Thread] = None
        self._stop_checking = False
        self._owns_daemon = False

    @property
    def status(self) -> str:
        """Get current daemon status"""
        return self._status

    def _set_status(self, status: str):
        """Set status and notify callback"""
        if self._status != status:
            self._status = status
            logger.info(f"Daemon status changed: {status}")
            if self.on_status_changed:
                self.on_status_changed(status)

    def is_running(self) -> bool:
        """Check if daemon is running"""
        try:
            import urllib.request

            try:
                response = urllib.request.urlopen(
                    f"http://{self.DAEMON_HOST}:{self.DAEMON_PORT}/status",
                    timeout=2.0,
                )
                return response.status == 200
            except Exception:
                # Also try with requests as fallback
                try:
                    import requests

                    response = requests.get(
                        f"http://{self.DAEMON_HOST}:{self.DAEMON_PORT}/status",
                        timeout=2.0,
                        proxies={"http": "", "https": ""},  # Disable proxies
                    )
                    return response.status_code == 200
                except Exception:
                    return False
        except Exception:
            return False

    def _kill_stale_daemon(self):
        """Kill any stale daemon process using the port"""
        try:
            # Try to read PID from file
            if self.DAEMON_PID_FILE.exists():
                try:
                    pid = int(self.DAEMON_PID_FILE.read_text().strip())
                    logger.info(f"Killing stale daemon process (PID: {pid})")
                    # Windows: use taskkill
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/F"],
                            capture_output=True,
                            timeout=5,
                        )
                    else:
                        # Unix: use kill
                        os.kill(pid, 9)
                    time.sleep(1)  # Wait for port to be released
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    pass

            # Also try HTTP stop request
            try:
                import requests

                requests.post(
                    f"http://{self.DAEMON_HOST}:{self.DAEMON_PORT}/stop",
                    timeout=1.0,
                )
            except Exception:
                pass

            time.sleep(0.5)  # Extra wait for socket cleanup
        except Exception as e:
            logger.warning(f"Could not kill stale daemon: {e}")

    def _resolve_python_executable(self) -> str:
        """Prefer a windowless Python executable on Windows for daemon launch."""
        current_executable = Path(sys.executable)
        if sys.platform != "win32":
            return str(current_executable)

        candidates = []
        if current_executable.name.lower() == "pythonw.exe":
            candidates.append(current_executable)
            candidates.append(current_executable.parent / "python.exe")
        else:
            candidates.append(current_executable.parent / "pythonw.exe")
            candidates.append(current_executable)

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return str(current_executable)

    def _creation_flags(self) -> int:
        """Return subprocess flags that keep the daemon hidden on Windows."""
        if sys.platform != "win32":
            return 0
        return subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    def start(self) -> bool:
        """Start the daemon in background"""
        try:
            if self.is_running():
                logger.info("Daemon already running")
                self._owns_daemon = False
                self._set_status("running")
                return True

            logger.info("Starting daemon...")
            self._set_status("starting")

            # Kill any stale daemon first
            self._kill_stale_daemon()

            python_exe = self._resolve_python_executable()

            # Start daemon subprocess - capture stderr for debugging
            log_file = PROJECT_ROOT / "daemon.log"
            with open(log_file, "w") as logf:
                self._daemon_process = subprocess.Popen(
                    [str(python_exe), "-m", "src.daemon"],
                    cwd=str(PROJECT_ROOT),
                    stdout=logf,
                    stderr=subprocess.STDOUT,
                    creationflags=self._creation_flags(),
                )
            self._owns_daemon = True

            # Save PID
            if self._daemon_process and self._daemon_process.pid:
                self.DAEMON_PID_FILE.write_text(str(self._daemon_process.pid))

            # Wait for daemon to start
            for attempt in range(15):
                time.sleep(0.5)
                if self.is_running():
                    logger.info("Daemon started successfully")
                    self._set_status("running")
                    return True

            logger.warning("Daemon started but not responding")
            # Try to read log to see what went wrong
            try:
                if log_file.exists():
                    log_content = log_file.read_text()
                    logger.error(f"Daemon startup logs:\n{log_content}")
            except Exception:
                pass
            self._owns_daemon = False
            self._set_status("error")
            return False

        except Exception as e:
            logger.error(f"Error starting daemon: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self._owns_daemon = False
            self._set_status("error")
            return False

    def stop(self, managed_only: bool = False) -> bool:
        """Stop the daemon"""
        try:
            if managed_only and not self._owns_daemon:
                logger.info(
                    "Skipping daemon stop because this instance does not own it"
                )
                return True
            if not self.is_running():
                logger.info("Daemon already stopped")
                self._owns_daemon = False
                self._set_status("stopped")
                return True

            logger.info("Stopping daemon...")
            self._set_status("stopping")

            # Try HTTP stop first
            try:
                import requests

                requests.post(
                    f"http://{self.DAEMON_HOST}:{self.DAEMON_PORT}/stop",
                    timeout=2.0,
                )
            except Exception:
                pass

            # Kill process if still running
            if self._daemon_process:
                try:
                    self._daemon_process.terminate()
                    self._daemon_process.wait(timeout=3)
                except Exception:
                    try:
                        self._daemon_process.kill()
                    except Exception:
                        pass

            # Clean up PID file
            if self.DAEMON_PID_FILE.exists():
                self.DAEMON_PID_FILE.unlink()

            self._daemon_process = None
            self._owns_daemon = False
            logger.info("Daemon stopped")
            self._set_status("stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping daemon: {e}")
            self._set_status("error")
            return False

    def check_status_background(self, interval: float = 2.0):
        """Start background thread to check daemon status"""
        self._stop_checking = False

        def _check():
            while not self._stop_checking:
                if self.is_running():
                    if self._status != "running":
                        self._set_status("running")
                else:
                    if self._status != "stopped":
                        self._set_status("stopped")
                time.sleep(interval)

        self._check_thread = threading.Thread(target=_check, daemon=True)
        self._check_thread.start()

    def stop_background_check(self):
        """Stop background status checker"""
        self._stop_checking = True
        if self._check_thread:
            self._check_thread.join(timeout=2)

    def get_status_display(self) -> str:
        """Get human-readable status"""
        status_map = {
            "running": "🟢 Daemon: Running",
            "stopped": "🔴 Daemon: Stopped",
            "starting": "🟡 Daemon: Starting...",
            "stopping": "🟡 Daemon: Stopping...",
            "error": "⚠️  Daemon: Error",
            "unknown": "❓ Daemon: Unknown",
        }
        return status_map.get(self._status, "❓ Daemon: Unknown")
