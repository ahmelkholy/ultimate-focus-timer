#!/usr/bin/env python3
"""
Session Manager for Enhanced Focus Timer
Core session logic, timing, and logging functionality
"""

import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class SessionType(Enum):
    """Types of focus sessions"""

    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    CUSTOM = "custom"


class SessionState(Enum):
    """Session states"""

    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"


class SessionManager:
    """Manages focus session timing, state, and logging"""

    def __init__(
        self, config_manager, music_controller=None, notification_manager=None
    ):
        """Initialize session manager with dependencies"""
        self.config = config_manager
        self.music = music_controller
        self.notifications = notification_manager

        # Session state
        self.session_type = SessionType.WORK
        self.session_duration = 0  # Total duration in seconds
        self.elapsed_seconds = 0  # Elapsed time in seconds
        self.state = SessionState.READY
        self.start_time = None
        self.pause_time = None

        # Timer thread
        self.timer_thread = None
        self.stop_event = threading.Event()

        # Callbacks for UI updates
        self.on_tick_callback = None
        self.on_complete_callback = None
        self.on_state_change_callback = None

        # Session tracking
        self.completed_work_sessions = 0
        self.session_count = 0

        # Ensure log directory exists
        self.log_dir = Path("log")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "focus.log"

    def set_callbacks(
        self,
        on_tick: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ):
        """Set callback functions for session events"""
        self.on_tick_callback = on_tick
        self.on_complete_callback = on_complete
        self.on_state_change_callback = on_state_change

    def start_session(
        self, session_type: SessionType, duration_minutes: Optional[int] = None
    ) -> bool:
        """Start a new focus session"""
        if self.state == SessionState.RUNNING:
            
            return False

        # Set session parameters
        self.session_type = session_type

        if duration_minutes is None:
            # Use default durations from config
            duration_map = {
                SessionType.WORK: self.config.get("work_mins", 25),
                SessionType.SHORT_BREAK: self.config.get("short_break_mins", 5),
                SessionType.LONG_BREAK: self.config.get("long_break_mins", 15),
                SessionType.CUSTOM: 25,  # Default for custom
            }
            duration_minutes = duration_map[session_type]

        self.session_duration = duration_minutes * 60
        self.elapsed_seconds = 0
        self.start_time = datetime.now()
        self.pause_time = None

        # Update state
        self._set_state(SessionState.RUNNING)

        # Start music for work sessions
        if session_type == SessionType.WORK and self.config.get(
            "classical_music", True
        ):
            self.music.start_music()

        # Show start notification
        self.notifications.show_session_start(session_type.value, duration_minutes)

        # Start timer thread
        self.stop_event.clear()
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()

        # Log session start
        self._log_session_event("Started", duration_minutes)

        
        return True

    def pause_session(self) -> bool:
        """Pause the current session"""
        if self.state != SessionState.RUNNING:
            return False

        self.pause_time = datetime.now()
        self._set_state(SessionState.PAUSED)

        # Pause music if it's playing
        if self.session_type == SessionType.WORK:
            self.music.pause_music()

        
        return True

    def resume_session(self) -> bool:
        """Resume a paused session"""
        if self.state != SessionState.PAUSED:
            return False

        self.pause_time = None
        self._set_state(SessionState.RUNNING)

        # Resume music if it was a work session
        if self.session_type == SessionType.WORK:
            self.music.resume_music()

        
        return True

    def stop_session(self) -> bool:
        """Stop the current session"""
        if self.state not in [SessionState.RUNNING, SessionState.PAUSED]:
            return False

        # Stop timer thread
        self.stop_event.set()
        if self.timer_thread:
            self.timer_thread.join(timeout=1)

        # Stop music
        self.music.stop_music()

        # Update state
        self._set_state(SessionState.STOPPED)

        # Log session stop
        completed_minutes = round(self.elapsed_seconds / 60, 1)
        self._log_session_event("Stopped", completed_minutes)

        
        return True

    def _timer_loop(self):
        """Main timer loop running in separate thread"""
        early_warning_sent = False
        early_warning_time = self.config.get("notify_early_warning", 2) * 60

        while (
            not self.stop_event.is_set()
            and self.elapsed_seconds < self.session_duration
        ):
            if self.state == SessionState.RUNNING:
                self.elapsed_seconds += 1

                # Check for early warning
                remaining_seconds = self.session_duration - self.elapsed_seconds
                if (
                    not early_warning_sent
                    and remaining_seconds <= early_warning_time
                    and remaining_seconds > 0
                ):

                    minutes_remaining = max(1, round(remaining_seconds / 60))
                    self.notifications.show_early_warning(
                        self.session_type.value, minutes_remaining
                    )
                    early_warning_sent = True

                # Call tick callback for UI updates
                if self.on_tick_callback:
                    try:
                        self.on_tick_callback(
                            self.elapsed_seconds, self.session_duration
                        )
                    except Exception as e:
                        print(f"Tick callback error: {e}")

            time.sleep(1)

        # Session completed if not stopped manually
        if (
            not self.stop_event.is_set()
            and self.elapsed_seconds >= self.session_duration
        ):
            self._complete_session()

    def _complete_session(self):
        """Handle session completion"""
        self._set_state(SessionState.COMPLETED)

        # Stop music if needed
        if self.session_type == SessionType.WORK and self.config.get(
            "pause_music_on_break", True
        ):
            self.music.stop_music()

        # Update session counters
        self.session_count += 1
        if self.session_type == SessionType.WORK:
            self.completed_work_sessions += 1

        # Show completion notification
        duration_minutes = self.session_duration // 60
        self.notifications.show_session_complete(
            self.session_type.value, duration_minutes
        )

        # Log completion
        self._log_session_event("Completed", duration_minutes)

        # Call completion callback
        if self.on_complete_callback:
            try:
                self.on_complete_callback(self.session_type, duration_minutes)
            except Exception as e:
                print(f"Complete callback error: {e}")

        

        # Auto-suggest next session
        self._suggest_next_session()

    def _suggest_next_session(self):
        """Auto-start or suggest the next appropriate session"""
        if self.session_type == SessionType.WORK:
            # Auto-start break after work session
            if self.config.get("auto_start_break", True):
                if (
                    self.completed_work_sessions
                    % self.config.get("long_break_interval", 4)
                    == 0
                ):
                    next_type = SessionType.LONG_BREAK
                    duration = self.config.get("long_break_mins", 15)
                else:
                    next_type = SessionType.SHORT_BREAK
                    duration = self.config.get("short_break_mins", 5)

                # Wait configured delay before starting next session
                import time

                delay = self.config.get("auto_start_delay", 2)
                time.sleep(delay)

                # Start the break session automatically
                self.start_session(next_type, duration)
            else:
                # Just suggest if auto-start is disabled
                if (
                    self.completed_work_sessions
                    % self.config.get("long_break_interval", 4)
                    == 0
                ):
                    next_type = SessionType.LONG_BREAK
                else:
                    next_type = SessionType.SHORT_BREAK
                print(
                    f"Consider starting a {next_type.value.replace('_', ' ')} session next"
                )
        else:
            # Handle break completion - only suggest, don't auto-start work
            if self.config.get("auto_start_work", False):
                next_type = SessionType.WORK
                duration = self.config.get("work_mins", 25)

                # Wait configured delay before starting next session
                import time

                delay = self.config.get("auto_start_delay", 2)
                time.sleep(delay)

                # Start the work session automatically
                self.start_session(next_type, duration)
            else:
                # Just suggest work session after break
                print("💡 Consider starting a work session next")

    def _set_state(self, new_state: SessionState):
        """Update session state and notify callbacks"""
        old_state = self.state
        self.state = new_state

        if self.on_state_change_callback and old_state != new_state:
            try:
                self.on_state_change_callback(old_state, new_state)
            except Exception as e:
                print(f"State change callback error: {e}")

    def _log_session_event(self, event: str, duration: float):
        """Log session event to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {event} {self.session_type.value} session ({duration} minutes)\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Logging error: {e}")

    def log_session(self, session_type: str, duration: int, status: str):
        """Log a session with the specified parameters"""
        # Convert session_type string to SessionType enum if needed
        if isinstance(session_type, str):
            type_mapping = {
                "work": SessionType.WORK,
                "short_break": SessionType.SHORT_BREAK,
                "long_break": SessionType.LONG_BREAK,
                "break": SessionType.SHORT_BREAK,  # Handle generic "break" type
                "custom": SessionType.CUSTOM,
            }
            if session_type in type_mapping:
                self.session_type = type_mapping[session_type]
            else:
                self.session_type = SessionType.WORK  # Default fallback

        # Log the session event
        self._log_session_event(status.title(), duration)

        # Update session counters if completed
        if status.lower() == "completed":
            self.session_count += 1
            if self.session_type == SessionType.WORK:
                self.completed_work_sessions += 1

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        remaining_seconds = max(0, self.session_duration - self.elapsed_seconds)
        progress_percent = (
            (self.elapsed_seconds / self.session_duration * 100)
            if self.session_duration > 0
            else 0
        )

        return {
            "type": self.session_type.value,
            "state": self.state.value,
            "duration_total": self.session_duration,
            "elapsed_seconds": self.elapsed_seconds,
            "remaining_seconds": remaining_seconds,
            "progress_percent": min(100, max(0, progress_percent)),
            "start_time": self.start_time,
            "pause_time": self.pause_time,
            "session_count": self.session_count,
            "completed_work_sessions": self.completed_work_sessions,
        }

    def get_time_display(self, show_seconds: bool = True) -> str:
        """Get formatted time display"""
        remaining_seconds = max(0, self.session_duration - self.elapsed_seconds)

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60

        if show_seconds:
            return f"{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:00"

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics from log file"""
        stats = {
            "total_sessions": 0,
            "work_sessions": 0,
            "break_sessions": 0,
            "total_work_time": 0,
            "total_break_time": 0,
            "average_work_session": 0,
            "average_break_session": 0,
            "today_sessions": 0,
            "today_work_time": 0,
        }

        if not self.log_file.exists():
            return stats

        try:
            today = datetime.now().date()

            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "Completed" in line:
                        stats["total_sessions"] += 1

                        # Parse session details
                        if "work session" in line:
                            stats["work_sessions"] += 1
                            # Extract duration
                            if "(" in line and "minutes)" in line:
                                duration_str = line.split("(")[1].split(" minutes)")[0]
                                try:
                                    duration = float(duration_str)
                                    stats["total_work_time"] += duration
                                except ValueError:
                                    pass

                        elif "break session" in line:
                            stats["break_sessions"] += 1
                            # Extract duration
                            if "(" in line and "minutes)" in line:
                                duration_str = line.split("(")[1].split(" minutes)")[0]
                                try:
                                    duration = float(duration_str)
                                    stats["total_break_time"] += duration
                                except ValueError:
                                    pass

                        # Check if today's session
                        if line.startswith(today.strftime("%Y-%m-%d")):
                            stats["today_sessions"] += 1
                            if "work session" in line:
                                if "(" in line and "minutes)" in line:
                                    duration_str = line.split("(")[1].split(
                                        " minutes)"
                                    )[0]
                                    try:
                                        duration = float(duration_str)
                                        stats["today_work_time"] += duration
                                    except ValueError:
                                        pass

            # Calculate averages
            if stats["work_sessions"] > 0:
                stats["average_work_session"] = (
                    stats["total_work_time"] / stats["work_sessions"]
                )

            if stats["break_sessions"] > 0:
                stats["average_break_session"] = (
                    stats["total_break_time"] / stats["break_sessions"]
                )

        except Exception as e:
            print(f"Error reading session statistics: {e}")

        return stats

    def cleanup(self):
        """Cleanup resources"""
        if self.state in [SessionState.RUNNING, SessionState.PAUSED]:
            self.stop_session()


if __name__ == "__main__":
    # Test session manager
    from config_manager import ConfigManager
    from music_controller import MusicController
    from notification_manager import NotificationManager

    print("Testing Session Manager...")
    print("=" * 50)

    config = ConfigManager()
    music = MusicController(config)
    notifications = NotificationManager(config)
    session_manager = SessionManager(config, music, notifications)

    # Test session info
    info = session_manager.get_session_info()
    print(f"Initial state: {info['state']}")

    # Test statistics
    stats = session_manager.get_session_statistics()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Work sessions: {stats['work_sessions']}")
    print(f"Today's work time: {stats['today_work_time']} minutes")

    # Interactive test
    test_session = (
        input("\nStart a test work session (5 seconds)? (y/n): ").lower().strip()
    )
    if test_session == "y":
        print("\nStarting test session...")

        def on_tick(elapsed, total):
            remaining = total - elapsed
            print(f"\rTime remaining: {remaining}s", end="", flush=True)

        def on_complete(session_type, duration):
            print(f"\n✅ Test session completed!")

        session_manager.set_callbacks(on_tick=on_tick, on_complete=on_complete)
        session_manager.start_session(
            SessionType.WORK, duration_minutes=5 / 60
        )  # 5 seconds

        # Wait for completion or manual stop
        try:
            while session_manager.state == SessionState.RUNNING:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping session...")
            session_manager.stop_session()

    session_manager.cleanup()
    print("\nSession manager test complete.")
