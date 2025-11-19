#!/usr/bin/env python3
"""
Ultimate Focus Timer - Cross-Platform Productivity Application
Main entry point with comprehensive functionality and cross-platform support
"""

import argparse
import os
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Dict

# --- Pre-launch Setup ---
# 1. Add src to path for local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


# 3. Define a global error logger
def log_error(exc_info):
    """Logs unhandled exceptions to a file."""
    log_file = Path(__file__).parent / "error.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=f)
        f.write("\n")
    print(
        f"FATAL ERROR: An unexpected error occurred. Details have been logged to {log_file}"
    )


def register_global_exception_handler():
    """Register a global handler to log fatal errors and notify the user."""

    def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log_error((exc_type, exc_value, exc_traceback))
        print("[X] Unexpected fatal error. Details have been logged to error.log.")

    sys.excepthook = _handle_unhandled_exception


# --- Main Application ---
from src.config_manager import ConfigManager
from src.focus_console import ConsoleInterface
from src.music_controller import MusicController
from src.notification_manager import NotificationManager
from src.session_manager import SessionManager


class UltimateFocusLauncher:
    """Ultimate cross-platform Focus Timer launcher"""

    def __init__(self):
        """Initialize the ultimate launcher"""
        self.config_manager = ConfigManager()
        # Initialize MusicController, NotificationManager, and SessionManager here
        # to ensure they are available when needed.
        # These are not lazy-loaded as they are core components.

        self.music_controller = MusicController(self.config_manager)
        self.notification_manager = NotificationManager(self.config_manager)
        self.session_manager = SessionManager(
            self.config_manager, self.music_controller, self.notification_manager
        )
        self.system_info = {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "os_release": platform.release(),
        }

    def check_dependencies(self) -> Dict[str, bool]:
        """Comprehensive dependency check"""
        dependencies = {
            "python": sys.version_info >= (3.8, 0),
            "tkinter": self._check_tkinter(),
            "yaml": self._check_module("yaml"),
            "plyer": self._check_module("plyer"),
            "psutil": self._check_module("psutil"),
            "matplotlib": self._check_module("matplotlib"),
            "pandas": self._check_module("pandas"),
            "mpv": self.music_controller.is_mpv_available(),
        }
        return dependencies

    def _check_module(self, module_name: str) -> bool:
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def _check_tkinter(self) -> bool:
        try:
            __import__("tkinter")
            return True
        except ImportError:
            return False

    def print_system_info(self):
        print("--- System Information ---")
        print("=" * 30)
        print(
            f"Platform: {self.system_info['platform']} ({self.system_info['architecture']})"
        )
        print(f"Python: {self.system_info['python_version']}")
        print(f"OS Release: {self.system_info['os_release']}")
        print(f"Working Directory: {Path.cwd()}")
        print()

    def print_dependency_status(self):
        dependencies = self.check_dependencies()
        print("--- Dependency Status ---")
        print("=" * 30)
        all_good = True
        for dep, status in dependencies.items():
            icon = "[V]" if status else "[X]"
            print(f"{icon} {dep.upper()}")
            if not status:
                all_good = False
                self._print_fix_suggestion(dep)
        print()
        if not all_good:
            print("--- Fix Issues ---")
            print("   Run: python -m pip install -r requirements.txt")
            if not dependencies.get("mpv", False):
                print("\n--- MPV Installation ---")
                self._print_mpv_install_instructions()
        else:
            print("[OK] All dependencies satisfied! Ready to focus!")
        print()

    def _print_fix_suggestion(self, dependency: str):
        suggestions = {
            "tkinter": "   - Install python3-tk (Linux) or use Python from python.org",
            "yaml": "   - pip install PyYAML",
            "plyer": "   - pip install plyer",
            "psutil": "   - pip install psutil",
            "matplotlib": "   - pip install matplotlib",
            "pandas": "   - pip install pandas",
            "mpv": "   - Install MPV media player for music support",
        }
        if dependency in suggestions:
            print(f"      {suggestions[dependency]}")

    def _print_mpv_install_instructions(self):
        system = platform.system()
        if system == "Windows":
            print("   Windows: choco install mpv OR winget install mpv")
        elif system == "Darwin":
            print("   macOS: brew install mpv")
        elif system == "Linux":
            print("   Linux: sudo apt install mpv OR sudo pacman -S mpv")
        else:
            print("   Visit: https://mpv.io/installation/")

    def _check_display_available(self) -> bool:
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return True
        if platform.system() == "Windows":
            return True
        if platform.system() == "Darwin":
            return not os.environ.get("SSH_CLIENT") and not os.environ.get("SSH_TTY")
        return False

    def launch_gui(self, show_splash: bool = False):
        if not self._check_display_available():
            print("[X] No GUI display available. Cannot launch GUI mode.")
            print("    You may be in a headless environment (like SSH or Docker).")
            print("    Try console mode: --console")
            return False
        if show_splash:
            self._show_splash()

        try:
            from src.focus_gui import FocusGUI

            app = FocusGUI()
            app.run()
            return True
        except Exception as e:
            log_error(sys.exc_info())
            print(f"[X] Error launching GUI: {e}")
            return False

    def launch_console(self):
        print("--- Launching Console Mode ---")
        try:
            console = ConsoleInterface()
            console.run()
        except Exception as e:
            log_error(sys.exc_info())
            print(f"[X] Error launching console: {e}")

    def launch_dashboard(self):
        print("--- Launching Analytics Dashboard ---")
        try:
            from src.dashboard import DashboardGUI, SessionAnalyzer

            analyzer = SessionAnalyzer()
            dashboard = DashboardGUI(analyzer)
            dashboard.run()
            print("--- Dashboard session completed. ---")
        except ImportError:
            print("[X] Dashboard dependencies (matplotlib, pandas) not found.")
            print("[>] Please install them: pip install matplotlib pandas")
        except KeyboardInterrupt:
            print("\n--- Dashboard interrupted by user. ---")
        except Exception as e:
            log_error(sys.exc_info())
            print(f"[X] Error launching dashboard: {e}")

    def run_quick_session(self, minutes: int = 25, session_type: str = "work"):
        print(f"--- Quick {session_type.title()} Session: {minutes} minutes ---")
        if self.config_manager.get("classical_music", True):
            self.music_controller.start_music()
        try:
            for remaining in range(minutes * 60, 0, -1):
                mins, secs = divmod(remaining, 60)
                print(
                    f"\rTime: {mins:02d}:{secs:02d} - Stay focused!", end="", flush=True
                )
                time.sleep(1)
            print("\n[OK] Session completed! Great work!")
            self.session_manager.log_session(session_type, minutes, "completed")
            self.notification_manager.show_notification(
                "Focus Session Complete!",
                f"{minutes}-minute {session_type} session finished.",
            )
        except KeyboardInterrupt:
            print("\n[!] Session paused by user.")
            self.session_manager.log_session(session_type, minutes, "interrupted")
        finally:
            self.music_controller.stop_music()

    def show_stats(self):
        print("--- Productivity Statistics ---")
        try:
            from src.dashboard import SessionAnalyzer

            analyzer = SessionAnalyzer()
            stats = analyzer.get_quick_stats()
            print(f"Today: {stats.get('today_sessions', 0)} sessions")
            print(f"This Week: {stats.get('week_sessions', 0)} sessions")
            print(f"Total: {stats.get('total_sessions', 0)} sessions")
            print(f"Total Time: {stats.get('total_minutes', 0)} minutes")
            if stats.get("streak", 0) > 0:
                print(f"Current Streak: {stats['streak']} days")
            else:
                print("Start your productivity streak today!")
        except ImportError:
            print("[X] Dashboard dependencies (matplotlib, pandas) not found.")
            print("[>] Please install them: pip install matplotlib pandas")

    def _show_splash(self):
        # for i in range(2):
        #     for frame in ["Loading   ", "Loading.  ", "Loading.. ", "Loading..."]:
        #         print(f"\rFocus Timer {frame}", end="", flush=True)
        #         time.sleep(0.3)
        # print()
        pass

    def interactive_launcher(self):
        while True:
            print("\n--- Ultimate Focus Timer ---")
            print("1. GUI Mode")
            print("2. Console Mode")
            print("3. Analytics Dashboard")
            print("4. Quick Session (25 min)")
            print("5. Quick Break (5 min)")
            print("6. Show Statistics")
            print("7. Check Dependencies")
            print("8. System Information")
            print("9. Exit")
            try:
                choice = input("Choose an option (1-9): ").strip()
                if choice == "1":
                    self.launch_gui()
                elif choice == "2":
                    self.launch_console()
                elif choice == "3":
                    self.launch_dashboard()
                elif choice == "4":
                    self.run_quick_session(25, "work")
                elif choice == "5":
                    self.run_quick_session(5, "break")
                elif choice == "6":
                    self.show_stats()
                elif choice == "7":
                    self.print_dependency_status()
                elif choice == "8":
                    self.print_system_info()
                elif choice == "9":
                    print("Thanks for using Focus Timer!")
                    break
                else:
                    print("[!] Invalid choice. Please try again.")
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            except Exception as e:
                log_error(sys.exc_info())
                print(f"[X] An unexpected error occurred in the launcher: {e}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Ultimate Focus Timer - Cross-Platform Productivity Application"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI version of the application",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Launch the console version of the application",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the analytics dashboard",
    )
    parser.add_argument(
        "--quick-session",
        type=int,
        metavar="MINUTES",
        help="Run a quick work session for specified minutes",
    )
    parser.add_argument(
        "--quick-break",
        type=int,
        metavar="MINUTES",
        help="Run a quick break session for specified minutes",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show productivity statistics",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check system dependencies",
    )
    parser.add_argument(
        "--sys-info",
        action="store_true",
        help="Display system information",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive CLI launcher (default if no other mode specified)",
    )

    args = parser.parse_args()

    launcher = UltimateFocusLauncher()

    if args.gui:
        launcher.launch_gui(show_splash=True)
    elif args.console:
        launcher.launch_console()
    elif args.dashboard:
        launcher.launch_dashboard()
    elif args.quick_session:
        launcher.run_quick_session(args.quick_session, "work")
    elif args.quick_break:
        launcher.run_quick_session(args.quick_break, "break")
    elif args.stats:
        launcher.show_stats()
    elif args.check_deps:
        launcher.print_dependency_status()
    elif args.sys_info:
        launcher.print_system_info()
    else:
        # Default to interactive launcher if no specific mode is requested
        launcher.interactive_launcher()


if __name__ == "__main__":
    register_global_exception_handler()
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
