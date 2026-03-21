#!/usr/bin/env python3
"""
Session Manager for Ultimate Focus Timer — Phase 2: Domain Isolation.

Pure, headless timer class with:
  - Full event-emitter pattern (no direct music/notification calls)
  - threading.Event-based pause (no busy-wait sleep)
  - Crash-recovery: auto-saves state every 10 s to a .state.json file
  - Clean session log written to app_paths.SESSION_LOG_FILE
"""

import json
import logging
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Optional

from .app_paths import PROJECT_ROOT, SESSION_LOG_FILE, LOG_DIR

logger = logging.getLogger(__name__)

# ── State persistence file ────────────────────────────────────────────────────
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

        # ── Timer state ───────────────────────────────────────────────────────
        self.session_type = SessionType.WORK
        self.session_duration: int = 0      # total seconds
        self.elapsed_seconds: int = 0
        self.state = SessionState.READY
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None

        # ── Threading ─────────────────────────────────────────────────────────
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()   # set = running, clear = paused

        # ── Event callbacks ───────────────────────────────────────────────────
        self._cb_session_start: Optional[Callable] = None
        self._cb_tick: Optional[Callable] = None
        self._cb_complete: Optional[Callable] = None
        self._cb_state_change: Optional[Callable] = None
        self._cb_early_warning: Optional[Callable] = None
        self._cb_pause: Optional[Callable] = None
        self._cb_resume: Optional[Callable] = None
        self._cb_stop: Optional[Callable] = None

        # ── Session counters ──────────────────────────────────────────────────
        self.completed_work_sessions: int = 0
        self.session_count: int = 0

        # ── Logging ───────────────────────────────────────────────────────────
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = SESSION_LOG_FILE

        # ── Crash-recovery auto-save ──────────────────────────────────────────
        self._auto_save_thread: Optional[threading.Thread] = None
        self._auto_save_stop = threading.Event()

        logger.debug("SessionManager ready (log=%s)", self.log_file)

    # ── Callback / event registration ────────────────────────────────────────

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
        """Register observer callbacks.  Only non-None values overwrite existing."""
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

    # ── Public session controls ───────────────────────────────────────────────

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
        logger.info("Session started: %s (%d min)", session_type.value, duration_minutes)
        return True

    def pause_session(self) -> bool:
        if self.state != SessionState.RUNNING:
            return False
        self.pause_time = datetime.now()
        self._pause_event.clear()         # stall the timer thread
        self._set_state(SessionState.PAUSED)
        self._emit("_cb_pause", self.session_type)
        logger.info("Session paused at %ds", self.elapsed_seconds)
        return True

    def resume_session(self) -> bool:
        if self.state != SessionState.PAUSED:
            return False
        self.pause_time = None
        self._pause_event.set()           # unblock timer thread
        self._set_state(SessionState.RUNNING)
        self._emit("_cb_resume", self.session_type)
        logger.info("Session resumed")
        return True

    def stop_session(self) -> bool:
        if self.state not in (SessionState.RUNNING, SessionState.PAUSED):
            return False

        self._stop_event.set()
        self._pause_event.set()           # unblock if paused

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)

        self._stop_auto_save()
        _STATE_FILE.unlink(missing_ok=True)   # clean exit

        elapsed = round(self.elapsed_seconds / 60, 1)
        self._set_state(SessionState.STOPPED)
        self._emit("_cb_stop", self.session_type, elapsed)
        self._log_event("Stopped", elapsed)
        logger.info("Session stopped after %.1f minutes", elapsed)
        return True

    # ── Timer loop ────────────────────────────────────────────────────────────

    def _timer_loop(self):
        early_warning_secs = self.config.get("notify_early_warning", 2) * 60
        early_warning_sent = False

        while (
            not self._stop_event.is_set()
            and self.elapsed_seconds < self.session_duration
        ):
            self._pause_event.wait()     # blocks without spin when paused
            if self._stop_event.is_set():
                break

            self.elapsed_seconds += 1
            remaining = self.session_duration - self.elapsed_seconds

            if not early_warning_sent and 0 < remaining <= early_warning_secs:
                self._emit("_cb_early_warning", self.session_type, max(1, round(remaining / 60)))
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
        return (
            self.config.get("auto_start_work", False),
            SessionType.WORK,
            self.config.get("work_mins", 25),
        )

    # ── State helpers ─────────────────────────────────────────────────────────

    def _set_state(self, new_state: SessionState):
        old = self.state
        self.state = new_state
        if old != new_state:
            self._emit("_cb_state_change", old, new_state)

    # ── Crash-recovery ────────────────────────────────────────────────────────

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
        """Return persisted state dict if crash-recovery file exists, else None."""
        if not _STATE_FILE.exists():
            return None
        try:
            data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            logger.info("Crash-recovery state found (saved at %s)", data.get("saved_at"))
            return data
        except (OSError, json.JSONDecodeError):
            logger.exception("Cannot parse crash-recovery state; discarding")
            _STATE_FILE.unlink(missing_ok=True)
            return None

    def clear_saved_state(self):
        _STATE_FILE.unlink(missing_ok=True)

    # ── Session log ───────────────────────────────────────────────────────────

    def _log_event(self, event: str, duration: float):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} - {event} {self.session_type.value} session ({duration} minutes)\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            logger.exception("Failed to write session log")

    # Legacy interface used by main.py quick sessions
    def log_session(self, session_type: str, duration: int, status: str):
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

    # ── Accessors ─────────────────────────────────────────────────────────────

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
