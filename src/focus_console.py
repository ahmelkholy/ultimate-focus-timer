#!/usr/bin/env python3
"""
Focus Console Manager
Command-line interface for the focus timer with advanced session management
"""

import argparse
import logging
import os
import threading
import time
from datetime import datetime
from typing import Optional

from .core import ConfigManager
from .core import SessionManager, SessionType
from .system import MusicController
from .system import NotificationManager

logger = logging.getLogger(__name__)


class ConsoleInterface:
    """Enhanced console interface for focus timer"""

    def __init__(self, config_path=None):
        self.config = ConfigManager(config_path)
        self.music_controller = MusicController(self.config)
        self.notification_manager = NotificationManager(self.config)
        # SessionManager is headless — console wires events itself
        self.session_manager = SessionManager(self.config)

        # Console state
        self.running = False
        self.display_thread = None
        self.last_status_lines = 0

        # Statistics tracking
        self.session_stats = {
            "sessions_completed": 0,
            "total_work_time": 0,
            "total_break_time": 0,
            "start_time": datetime.now(),
        }

        # Wire all session events
        self.session_manager.set_callbacks(
            on_tick=self._on_timer_tick,
            on_complete=self._on_session_completed,
            on_state_change=self._on_state_change,
            on_session_start=self._on_session_started,
            on_early_warning=self._on_early_warning,
            on_pause=self._on_paused,
            on_resume=self._on_resumed,
            on_stop=self._on_stopped,
        )

    # ── Session event handlers ────────────────────────────────────────────────

    def _on_session_started(self, session_type, duration_minutes):
        if session_type == SessionType.WORK and self.config.get("classical_music", True):
            self.music_controller.start_music()
        self.notification_manager.show_session_start(session_type.value, duration_minutes)

    def _on_session_completed(self, session_type, duration_minutes):
        self.session_stats["sessions_completed"] += 1
        if session_type == SessionType.WORK:
            self.session_stats["total_work_time"] += duration_minutes
        else:
            self.session_stats["total_break_time"] += duration_minutes
        self.music_controller.stop_music()

    def _on_early_warning(self, session_type, minutes_remaining):
        self.notification_manager.show_early_warning(session_type.value, minutes_remaining)

    def _on_paused(self, session_type):
        if session_type == SessionType.WORK:
            self.music_controller.pause_music()

    def _on_resumed(self, session_type):
        if session_type == SessionType.WORK:
            self.music_controller.resume_music()

    def _on_stopped(self, session_type, elapsed_minutes):
        self.music_controller.stop_music()

    def run(self):
        """Main entry point for console interface"""
        self.run_interactive()

    def _clear_status_lines(self):
        """Clear the last status display"""
        if self.last_status_lines > 0:
            # Move cursor up and clear lines
            for _ in range(self.last_status_lines):
                print("\033[A\033[K", end="")
            self.last_status_lines = 0

    def _print_header(self):
        """Print the application header"""
        os.system("cls" if os.name == "nt" else "clear")
        print("═" * 70)
        print("                     🎯 FOCUS TIMER")
        print("                   Console Manager")
        print("═" * 70)
        print()

    def _print_session_info(self):
        """Print current session information"""
        status = self.session_manager.get_session_info()
        config = self.config.get_timer_config()

        # Session type and duration
        session_type = status.get("type", "work")
        if session_type == "work":
            total_duration = config["work_duration"]
            icon = "💼"
            type_name = "Work Session"
        elif session_type == "short_break":
            total_duration = config["short_break_duration"]
            icon = "☕"
            type_name = "Short Break"
        elif session_type == "long_break":
            total_duration = config["long_break_duration"]
            icon = "🌳"
            type_name = "Long Break"
        else:
            total_duration = 25
            icon = "⏰"
            type_name = "Session"

        elapsed = status.get("elapsed_seconds", 0)
        remaining = max(0, total_duration * 60 - elapsed)

        # Format time
        elapsed_min, elapsed_sec = divmod(elapsed, 60)
        remaining_min, remaining_sec = divmod(remaining, 60)

        # Progress bar
        progress = min(1.0, elapsed / (total_duration * 60))
        bar_length = 40
        filled_length = int(bar_length * progress)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # Status display
        state = status.get("state", "idle")
        state_icon = {
            "running": "▶️",
            "paused": "⏸️",
            "completed": "✅",
            "idle": "⏹️",
        }.get(state, "❓")

        print(f"{icon} {type_name}")
        print(f"Status: {state_icon} {state.title()}")
        print(f"Progress: [{bar}] {progress:.1%}")
        print(
            f"Elapsed: {elapsed_min:02d}:{elapsed_sec:02d} | Remaining: {remaining_min:02d}:{remaining_sec:02d}"
        )
        print()

    def _print_statistics(self):
        """Print session statistics"""
        total_time = (
            datetime.now() - self.session_stats["start_time"]
        ).total_seconds() / 60

        print("📊 SESSION STATISTICS")
        print(f"├─ Sessions Completed: {self.session_stats['sessions_completed']}")
        print(f"├─ Total Work Time: {self.session_stats['total_work_time']:.1f} min")
        print(f"├─ Total Break Time: {self.session_stats['total_break_time']:.1f} min")
        print(f"├─ Total Runtime: {total_time:.1f} min")

        if self.session_stats["sessions_completed"] > 0:
            avg_session = (
                self.session_stats["total_work_time"]
                / self.session_stats["sessions_completed"]
            )
            print(f"└─ Avg Session Length: {avg_session:.1f} min")
        else:
            print("└─ Avg Session Length: 0.0 min")
        print()

    def _print_music_status(self):
        """Print music player status"""
        if self.music_controller.is_playing:
            print("🎵 Classical music playing...")
        else:
            print("🔇 Music: Off")
        print()

    def _print_controls(self):
        """Print available controls"""
        status = self.session_manager.get_session_info()
        state = status.get("state", "idle")

        print("🎮 CONTROLS")

        if state == "idle":
            print("├─ [S] Start Session")
        elif state == "running":
            print("├─ [P] Pause Session")
            print("├─ [X] Stop Session")
        elif state == "paused":
            print("├─ [R] Resume Session")
            print("├─ [X] Stop Session")
        elif state == "completed":
            print("├─ [S] Start Next Session")

        print("├─ [M] Toggle Music")
        print("├─ [T] Show Statistics")
        print("├─ [C] Configuration")
        print("├─ [H] Help")
        print("└─ [Q] Quit")
        print()

    def _print_help(self):
        """Print help information"""
        print("🆘 HELP")
        print("├─ Focus Timer uses the Pomodoro Technique")
        print("├─ Work sessions are followed by short breaks")
        print("├─ Every 4th session includes a long break")
        print("├─ Auto-start breaks: Enabled (configurable)")
        print("├─ Session controls: [P]ause, [R]esume, [S]top")
        print("├─ Classical music helps maintain focus")
        print("├─ All sessions are logged for analytics")
        print("└─ Press any key to continue...")
        input()

    def _print_configuration(self):
        """Print current configuration"""
        timer_config = self.config.get_timer_config()
        music_config = self.config.get_music_config()

        print("⚙️  CONFIGURATION")
        print("Timer Settings:")
        print(f"├─ Work Duration: {timer_config['work_duration']} min")
        print(f"├─ Short Break: {timer_config['short_break_duration']} min")
        print(f"├─ Long Break: {timer_config['long_break_duration']} min")
        print(
            f"├─ Sessions until Long Break: {timer_config['sessions_until_long_break']}"
        )
        print(f"├─ Auto-start Breaks: {timer_config['auto_start_breaks']}")
        print(f"└─ Auto-start Work: {timer_config['auto_start_work']}")
        print()
        print("Music Settings:")
        print(f"├─ Enabled: {music_config['enabled']}")
        print(f"├─ Volume: {music_config['volume']}")
        print(f"├─ Shuffle: {music_config['shuffle']}")
        print(f"└─ Repeat: {music_config['repeat']}")
        print()
        print("Press any key to continue...")
        input()

    def _display_status(self):
        """Display the main status screen"""
        while self.running:
            self._clear_status_lines()

            # Count lines for clearing
            lines_count = 0

            self._print_session_info()
            lines_count += 6

            self._print_statistics()
            lines_count += 7

            self._print_music_status()
            lines_count += 2

            self._print_controls()
            lines_count += 8

            print("Enter command: ", end="", flush=True)
            lines_count += 1

            self.last_status_lines = lines_count
            time.sleep(1)

    def _on_timer_tick(self, elapsed: int, remaining: int):
        """Handle timer tick callback"""
        # Optionally update display more frequently
        pass

    def _on_state_change(self, old_state, new_state):
        """Handle session state change callback"""
        # You can add specific logic here for state transitions if needed
        pass

    def _handle_command(self, command: str):
        """Handle user commands"""
        command = command.lower().strip()

        if command == "q":
            return False
        elif command == "s":
            # Start a work session by default, or next appropriate session
            self.session_manager.start_session(SessionType.WORK)
        elif command == "p":
            self.session_manager.pause_session()
        elif command == "r":
            self.session_manager.resume_session()
        elif command == "x":
            self.session_manager.stop_session()
        elif command == "m":
            if self.music_controller.is_playing:
                self.music_controller.stop_music()
            else:
                self.music_controller.start_music()
        elif command == "t":
            self._print_header()
            self._print_statistics()
            print("Press any key to continue...")
            input()
        elif command == "c":
            self._print_header()
            self._print_configuration()
        elif command == "h":
            self._print_header()
            self._print_help()
        elif command == "":
            pass  # Just refresh the display
        else:
            print(f"Unknown command: {command}")
            time.sleep(1)

        return True

    def run_interactive(self):
        """Run the interactive console interface"""
        self._print_header()
        print("🚀 Starting Focus Timer Console...")
        print("Type 'h' for help or 'q' to quit")
        print()
        time.sleep(2)

        self.running = True

        # Start display thread
        self.display_thread = threading.Thread(target=self._display_status, daemon=True)
        self.display_thread.start()

        try:
            while self.running:
                # Get user input
                try:
                    command = input()
                    if not self._handle_command(command):
                        break
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break

        finally:
            self.running = False
            self.session_manager.stop_session()
            self.music_controller.stop_music()
            print("\n👋 Goodbye! Keep up the great work!")

    def run_command(
        self, action: str, duration: Optional[int] = None, session_type: str = "work"
    ):
        """Run a single command non-interactively"""
        if action == "start":
            # Convert session type string to SessionType enum
            session_type_map = {
                "work": SessionType.WORK,
                "short_break": SessionType.SHORT_BREAK,
                "long_break": SessionType.LONG_BREAK,
                "break": SessionType.SHORT_BREAK,  # Alias for short break
            }

            session_type_enum = session_type_map.get(session_type, SessionType.WORK)

            if duration:
                # Override default duration
                timer_config = self.config.get_timer_config()
                if session_type == "work":
                    timer_config["work_duration"] = duration
                elif session_type == "short_break":
                    timer_config["short_break_duration"] = duration
                elif session_type == "long_break":
                    timer_config["long_break_duration"] = duration

                self.config.update_timer_config(timer_config)

            print(f"🚀 Starting {session_type.replace('_', ' ')} session...")
            self.session_manager.start_session(session_type_enum, duration)

            # Wait for session to complete
            while self.session_manager.get_session_info()["state"] in [
                "running",
                "paused",
            ]:
                time.sleep(1)

            print("✅ Session completed!")

        elif action == "status":
            status = self.session_manager.get_session_info()
            print(f"Session Status: {status['state']}")
            if status["state"] != "ready":
                print(f"Type: {status['type']}")
                print(f"Elapsed: {status['elapsed_seconds']}s")
                print(f"Remaining: {status['remaining_seconds']}s")

        elif action == "stats":
            from .dashboard import console_dashboard

            console_dashboard("all")

        elif action == "stop":
            self.session_manager.stop_session()
            print("⏹️ Session stopped")

        else:
            print(f"Unknown action: {action}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Focus Timer Console Manager")

    # Mode selection
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode (default)",
    )
    parser.add_argument("--config", "-c", type=str, help="Path to configuration file")

    # Command mode options
    parser.add_argument(
        "--action",
        choices=["start", "stop", "status", "stats"],
        help="Action to perform (non-interactive mode)",
    )
    parser.add_argument(
        "--duration", "-d", type=int, help="Session duration in minutes"
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["work", "short_break", "long_break"],
        default="work",
        help="Session type",
    )

    # Quick start options
    parser.add_argument(
        "--work",
        type=int,
        metavar="MINUTES",
        help="Start a work session for specified minutes",
    )
    parser.add_argument(
        "--break",
        type=int,
        metavar="MINUTES",
        help="Start a break session for specified minutes",
    )
    parser.add_argument(
        "--pomodoro",
        action="store_true",
        help="Start a standard 25-minute Pomodoro session",
    )

    args = parser.parse_args()

    # Create console interface
    console = ConsoleInterface(args.config)

    # Handle quick start options
    if args.work:
        console.run_command("start", args.work, "work")
    elif getattr(args, "break"):
        console.run_command("start", getattr(args, "break"), "short_break")
    elif args.pomodoro:
        console.run_command("start", 25, "work")
    elif args.action:
        console.run_command(args.action, args.duration, args.type)
    else:
        # Default to interactive mode
        console.run_interactive()


if __name__ == "__main__":
    main()
