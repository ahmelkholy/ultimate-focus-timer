#!/usr/bin/env python3
"""
Ultimate Focus Timer CLI Module
Advanced command-line interface with rich terminal output
"""

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_manager import ConfigManager
    from dashboard import SessionAnalyzer
    from music_controller import MusicController
    from notification_manager import NotificationManager
    from session_manager import SessionManager
    from task_manager import TaskManager
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)


class UltimateCLI:
    """Advanced CLI interface with rich output support"""

    def __init__(self):
        """Initialize the CLI with rich console if available"""
        if RICH_AVAILABLE:
            self.console = Console()
            self.use_rich = True
        else:
            self.console = None
            self.use_rich = False

        # Initialize core components
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager()
        self.music_controller = MusicController(self.config_manager)
        self.notification_manager = NotificationManager()
        self.session_analyzer = SessionAnalyzer()
        self.task_manager = TaskManager()

    def print(self, *args, **kwargs):
        """Enhanced print function that uses rich if available"""
        if self.use_rich and self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def show_banner(self):
        """Display application banner"""
        if self.use_rich:
            banner = """
🎯 Ultimate Focus Timer CLI
Cross-Platform Productivity Suite
"""
            panel = Panel(banner.strip(), expand=False, border_style="bright_blue")
            self.console.print(panel)
        else:
            print("🎯 Ultimate Focus Timer CLI")
            print("Cross-Platform Productivity Suite")
            print("=" * 40)

    def show_system_status(self):
        """Display comprehensive system status"""
        if self.use_rich:
            # Create system status table
            table = Table(
                title="System Status", show_header=True, header_style="bold magenta"
            )
            table.add_column("Component", style="cyan", width=20)
            table.add_column("Status", width=15)
            table.add_column("Details", style="dim")

            # Check dependencies
            dependencies = {
                "Python": sys.version.split()[0],
                "YAML": self._check_module("yaml"),
                "Plyer": self._check_module("plyer"),
                "Matplotlib": self._check_module("matplotlib"),
                "Pandas": self._check_module("pandas"),
                "Rich": RICH_AVAILABLE,
                "MPV": self.music_controller.is_mpv_available(),
            }

            for component, status in dependencies.items():
                if isinstance(status, bool):
                    status_text = (
                        "[green]✓ Available[/green]"
                        if status
                        else "[red]✗ Missing[/red]"
                    )
                    detail = "Working" if status else "Not installed"
                else:
                    status_text = "[green]✓ Available[/green]"
                    detail = str(status)

                table.add_row(component, status_text, detail)

            self.console.print(table)
        else:
            print("\nSystem Status:")
            print("-" * 20)
            print(f"Python: {sys.version.split()[0]}")
            print(f"Rich UI: {'Available' if RICH_AVAILABLE else 'Not available'}")
            print(
                f"MPV: {'Available' if self.music_controller.is_mpv_available() else 'Not available'}"
            )

    def _check_module(self, module_name: str) -> bool:
        """Check if a module is available"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def show_productivity_stats(self, days: int = 7):
        """Display productivity statistics"""
        stats = self.session_analyzer.get_detailed_stats(days)

        if self.use_rich:
            # Create stats table
            table = Table(
                title=f"Productivity Stats (Last {days} days)", show_header=True
            )
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bold")
            table.add_column("Details", style="dim")

            # Add stats rows
            table.add_row(
                "Total Sessions",
                str(stats.get("total_sessions", 0)),
                "Completed focus sessions",
            )
            table.add_row(
                "Total Time",
                f"{stats.get('total_minutes', 0)} min",
                "Time spent focusing",
            )
            table.add_row(
                "Average Session",
                f"{stats.get('avg_session_length', 0):.1f} min",
                "Average session length",
            )
            table.add_row(
                "Today's Sessions",
                str(stats.get("today_sessions", 0)),
                "Sessions completed today",
            )
            table.add_row(
                "Current Streak",
                f"{stats.get('streak', 0)} days",
                "Consecutive active days",
            )

            self.console.print(table)

            # Show daily breakdown if available
            if "daily_breakdown" in stats and stats["daily_breakdown"]:
                daily_table = Table(title="Daily Breakdown", show_header=True)
                daily_table.add_column("Date", style="cyan")
                daily_table.add_column("Sessions", justify="right")
                daily_table.add_column("Minutes", justify="right")

                for day_data in stats["daily_breakdown"][-7:]:  # Last 7 days
                    daily_table.add_row(
                        day_data.get("date", "Unknown"),
                        str(day_data.get("sessions", 0)),
                        str(day_data.get("minutes", 0)),
                    )

                self.console.print(daily_table)
        else:
            print("\nProductivity Statistics:")
            print("-" * 30)
            print(f"Total Sessions: {stats.get('total_sessions', 0)}")
            print(f"Total Time: {stats.get('total_minutes', 0)} minutes")
            print(f"Today's Sessions: {stats.get('today_sessions', 0)}")
            print(f"Current Streak: {stats.get('streak', 0)} days")

    def run_focus_session(
        self, minutes: int, session_type: str = "work", with_music: bool = None
    ):
        """Run a focus session with enhanced CLI display"""
        if with_music is None:
            with_music = self.config_manager.get("classical_music", True)

        # Start music if enabled
        if with_music:
            self.music_controller.start_music()
            if self.use_rich:
                self.console.print("🎵 Classical music started", style="green")
            else:
                print("🎵 Classical music started")

        # Session start
        start_time = datetime.now()
        total_seconds = minutes * 60

        if self.use_rich:
            self._run_rich_session(minutes, session_type, total_seconds, start_time)
        else:
            self._run_basic_session(minutes, session_type, total_seconds)

        # Stop music
        if with_music:
            self.music_controller.stop_music()

        # Log session
        self.session_manager.log_session(session_type, minutes, "completed")

        # Show completion notification
        if self.use_rich:
            completion_panel = Panel(
                f"🎉 {session_type.title()} session completed!\n"
                f"Duration: {minutes} minutes\n"
                f"Great work! Keep up the momentum! 💪",
                title="Session Complete",
                border_style="green",
            )
            self.console.print(completion_panel)
        else:
            print(f"\n🎉 {session_type.title()} session completed!")
            print(f"Duration: {minutes} minutes")

        # Show notification
        self.notification_manager.show_notification(
            "Focus Session Complete!",
            f"{minutes}-minute {session_type} session finished",
        )

    def _run_rich_session(
        self, minutes: int, session_type: str, total_seconds: int, start_time: datetime
    ):
        """Run session with rich progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        ) as progress:

            task = progress.add_task(
                f"🎯 {session_type.title()} Session ({minutes} min)",
                total=total_seconds,
            )

            try:
                for elapsed in range(total_seconds + 1):
                    progress.update(task, advance=1)
                    time.sleep(1)

                    # Update description with remaining time
                    remaining = total_seconds - elapsed
                    mins, secs = divmod(remaining, 60)
                    progress.update(
                        task,
                        description=f"🎯 {session_type.title()} Session - {mins:02d}:{secs:02d} remaining",
                    )

            except KeyboardInterrupt:
                progress.update(task, description="⏸️ Session paused by user")
                self.console.print("\n⏸️ Session interrupted by user", style="yellow")
                self.session_manager.log_session(session_type, minutes, "interrupted")
                raise

    def _run_basic_session(self, minutes: int, session_type: str, total_seconds: int):
        """Run session with basic progress display"""
        try:
            for remaining in range(total_seconds, 0, -1):
                mins, secs = divmod(remaining, 60)
                progress = ((total_seconds - remaining) / total_seconds) * 100
                print(
                    f"\r🎯 {session_type.title()} Session: {mins:02d}:{secs:02d} ({progress:.1f}%)",
                    end="",
                    flush=True,
                )
                time.sleep(1)

            print("\n")  # New line after completion

        except KeyboardInterrupt:
            print("\n⏸️ Session interrupted by user")
            self.session_manager.log_session(session_type, minutes, "interrupted")
            raise

    def interactive_mode(self):
        """Interactive CLI mode with menu system"""
        while True:
            if self.use_rich:
                self._show_rich_menu()
            else:
                self._show_basic_menu()

            try:
                if self.use_rich:
                    choice = Prompt.ask(
                        "Choose an option",
                        choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
                    )
                else:
                    choice = input("Choose an option (1-9): ").strip()

                if choice == "1":
                    minutes = self._get_session_duration("work")
                    self.run_focus_session(minutes, "work")
                elif choice == "2":
                    minutes = self._get_session_duration("break")
                    self.run_focus_session(minutes, "break")
                elif choice == "3":
                    self._custom_session()
                elif choice == "4":
                    self.show_productivity_stats()
                elif choice == "5":
                    self._show_config()
                elif choice == "6":
                    self._edit_config()
                elif choice == "7":
                    self.show_system_status()
                elif choice == "8":
                    self._show_help()
                elif choice == "9":
                    if self.use_rich:
                        self.console.print(
                            "👋 Thanks for using Focus Timer!", style="bright_green"
                        )
                    else:
                        print("👋 Thanks for using Focus Timer!")
                    break
                else:
                    if self.use_rich:
                        self.console.print(
                            "❌ Invalid choice. Please try again.", style="red"
                        )
                    else:
                        print("❌ Invalid choice. Please try again.")

            except KeyboardInterrupt:
                if self.use_rich:
                    self.console.print("\n👋 Goodbye!", style="bright_green")
                else:
                    print("\n👋 Goodbye!")
                break
            except Exception as e:
                if self.use_rich:
                    self.console.print(f"❌ Error: {e}", style="red")
                else:
                    print(f"❌ Error: {e}")

    def _show_rich_menu(self):
        """Show interactive menu with rich formatting"""
        menu_text = """
[bold cyan]🎯 Ultimate Focus Timer CLI[/bold cyan]

[bold]Session Options:[/bold]
1. 🎯 Work Session (25 min default)
2. ☕ Break Session (5 min default)
3. ⚙️  Custom Session

[bold]Analytics & Info:[/bold]
4. 📊 Productivity Statistics
5. 📋 Show Configuration
6. ✏️  Edit Configuration

[bold]System:[/bold]
7. 🔍 System Status
8. ❓ Help & Usage
9. 🚪 Exit
"""
        panel = Panel(menu_text.strip(), border_style="bright_blue")
        self.console.print(panel)

    def _show_basic_menu(self):
        """Show basic text menu"""
        print("\n🎯 Ultimate Focus Timer CLI")
        print("=" * 30)
        print("1. 🎯 Work Session (25 min)")
        print("2. ☕ Break Session (5 min)")
        print("3. ⚙️  Custom Session")
        print("4. 📊 Statistics")
        print("5. 📋 Show Config")
        print("6. ✏️  Edit Config")
        print("7. 🔍 System Status")
        print("8. ❓ Help")
        print("9. 🚪 Exit")
        print()

    def _get_session_duration(self, session_type: str) -> int:
        """Get session duration from user or config"""
        default_duration = self.config_manager.get(
            f"{session_type}_mins", 25 if session_type == "work" else 5
        )

        if self.use_rich:
            duration_str = Prompt.ask(
                f"Duration for {session_type} session", default=str(default_duration)
            )
        else:
            duration_str = input(
                f"Duration for {session_type} session ({default_duration} min): "
            ).strip()
            if not duration_str:
                duration_str = str(default_duration)

        try:
            return int(duration_str)
        except ValueError:
            if self.use_rich:
                self.console.print("❌ Invalid duration, using default", style="yellow")
            else:
                print("❌ Invalid duration, using default")
            return default_duration

    def _custom_session(self):
        """Create a custom session"""
        if self.use_rich:
            session_type = Prompt.ask(
                "Session type", choices=["work", "break", "custom"], default="work"
            )
            duration = int(Prompt.ask("Duration (minutes)", default="25"))
            with_music = Confirm.ask("Play classical music?", default=True)
        else:
            session_type = (
                input("Session type (work/break/custom) [work]: ").strip() or "work"
            )
            duration = int(input("Duration (minutes) [25]: ").strip() or "25")
            with_music_input = (
                input("Play classical music? (y/n) [y]: ").strip().lower()
            )
            with_music = with_music_input != "n"

        self.run_focus_session(duration, session_type, with_music)

    def _show_config(self):
        """Display current configuration"""
        config = self.config_manager.config

        if self.use_rich:
            table = Table(title="Current Configuration", show_header=True)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="bold")
            table.add_column("Description", style="dim")

            config_descriptions = {
                "work_mins": "Work session duration",
                "short_break_mins": "Short break duration",
                "long_break_mins": "Long break duration",
                "classical_music": "Enable classical music",
                "classical_music_volume": "Music volume level",
                "notify": "Enable notifications",
            }

            for key, value in config.items():
                description = config_descriptions.get(key, "Custom setting")
                table.add_row(key, str(value), description)

            self.console.print(table)
        else:
            print("\nCurrent Configuration:")
            print("-" * 25)
            for key, value in config.items():
                print(f"{key}: {value}")

    def _edit_config(self):
        """Edit configuration interactively"""
        if self.use_rich:
            self.console.print("⚙️ Configuration Editor", style="bold cyan")
            setting = Prompt.ask(
                "Which setting to edit?",
                choices=list(self.config_manager.config.keys()) + ["cancel"],
            )

            if setting == "cancel":
                return

            current_value = self.config_manager.get(setting)
            new_value = Prompt.ask(
                f"New value for {setting}", default=str(current_value)
            )

            # Type conversion
            if isinstance(current_value, bool):
                new_value = new_value.lower() in ["true", "yes", "y", "1"]
            elif isinstance(current_value, int):
                new_value = int(new_value)
            elif isinstance(current_value, float):
                new_value = float(new_value)

            self.config_manager.set(setting, new_value)
            self.config_manager.save_config()

            self.console.print(f"✅ Updated {setting} = {new_value}", style="green")
        else:
            print("\n⚙️ Configuration Editor")
            print("Available settings:", ", ".join(self.config_manager.config.keys()))
            setting = input("Which setting to edit? ").strip()

            if setting in self.config_manager.config:
                current_value = self.config_manager.get(setting)
                new_value = input(
                    f"New value for {setting} [{current_value}]: "
                ).strip()

                if new_value:
                    # Simple type conversion
                    if isinstance(current_value, bool):
                        new_value = new_value.lower() in ["true", "yes", "y", "1"]
                    elif isinstance(current_value, int):
                        new_value = int(new_value)
                    elif isinstance(current_value, float):
                        new_value = float(new_value)

                    self.config_manager.set(setting, new_value)
                    self.config_manager.save_config()
                    print(f"✅ Updated {setting} = {new_value}")

    def _show_help(self):
        """Show help information"""
        help_text = """
🎯 Ultimate Focus Timer CLI - Help

QUICK COMMANDS:
  python main.py --quick 25        # 25-minute focus session
  python main.py --break 5         # 5-minute break
  python main.py --stats           # Show statistics
  python main.py --check           # Check dependencies

INTERACTIVE MODE:
  Run 'python main.py --console' to enter interactive mode

FEATURES:
  • Pomodoro timer with customizable durations
  • Classical music integration (requires MPV)
  • Productivity analytics and statistics
  • Cross-platform notifications
  • Session logging and streak tracking

CONFIGURATION:
  Edit config.yml or use the built-in configuration editor

For more information, visit the project documentation.
"""

        if self.use_rich:
            panel = Panel(help_text.strip(), title="Help & Usage", border_style="blue")
            self.console.print(panel)
        else:
            print(help_text)

    def show_tasks(self):
        """Display today's tasks in a table."""
        tasks = self.task_manager.get_today_tasks()
        if not tasks:
            self.print("[yellow]No tasks for today. Add one with --add-task.[/yellow]")
            return

        if self.use_rich:
            table = Table(title="Today's Tasks", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim", width=4)
            table.add_column("Task", style="cyan", no_wrap=True)
            table.add_column("Status", width=12)
            table.add_column("Pomodoros", justify="right")

            for task in tasks:
                status = "✅ Completed" if task.completed else "⏳ Pending"
                pomodoros = f"{task.pomodoros_completed}/{task.pomodoros_planned}"
                table.add_row(str(task.id.split('_')[-1]), task.title, status, pomodoros)
            self.console.print(table)
        else:
            print("\nToday's Tasks:")
            for task in tasks:
                status = "Completed" if task.completed else "Pending"
                print(f"- {task.title} ({status})")

    def add_task(self, title: str):
        """Add a new task."""
        if not title:
            self.print("[red]Cannot add a task with an empty title.[/red]")
            return
        task = self.task_manager.add_task(title)
        self.print(f"[green]✓ Added task:[/green] '{task.title}'")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ultimate Focus Timer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )
    parser.add_argument(
        "--stats", "-s", action="store_true", help="Show productivity statistics"
    )
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument(
        "--work", type=int, metavar="MINUTES", help="Start work session"
    )
    parser.add_argument(
        "--break", type=int, metavar="MINUTES", help="Start break session"
    )
    parser.add_argument(
        "--no-music", action="store_true", help="Disable music for this session"
    )
    parser.add_argument("--tasks", action="store_true", help="Show today's tasks")
    parser.add_argument("--add-task", type=str, metavar='TITLE', help="Add a new task")

    args = parser.parse_args()

    cli = UltimateCLI()

    # Show banner
    cli.show_banner()

    try:
        if args.stats:
            cli.show_productivity_stats()
        elif args.status:
            cli.show_system_status()
        elif args.work:
            cli.run_focus_session(args.work, "work", not args.no_music)
        elif getattr(args, "break"):
            cli.run_focus_session(getattr(args, "break"), "break", not args.no_music)
        elif args.tasks:
            cli.show_tasks()
        elif args.add_task:
            cli.add_task(args.add_task)
        elif args.interactive:
            cli.interactive_mode()
        else:
            cli.interactive_mode()

    except KeyboardInterrupt:
        if cli.use_rich:
            cli.console.print(
                "\n👋 Session interrupted. See you next time!", style="bright_yellow"
            )
        else:
            print("\n👋 Session interrupted. See you next time!")
    except Exception as e:
        if cli.use_rich:
            cli.console.print(f"❌ Unexpected error: {e}", style="red")
        else:
            print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
