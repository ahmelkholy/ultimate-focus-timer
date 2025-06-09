#!/usr/bin/env python3
"""
Ultimate Focus Timer - Cross-Platform Productivity Application
Main entry point with comprehensive functionality and cross-platform support
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add current directory and src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config_manager import ConfigManager
    from dashboard import DashboardGUI, SessionAnalyzer
    from focus_console import ConsoleInterface
    from focus_gui import FocusGUI
    from music_controller import MusicController
    from notification_manager import NotificationManager
    from session_manager import SessionManager
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("📦 Please ensure all required modules are available.")
    print("🔧 Run: python -m pip install -r requirements.txt")
    sys.exit(1)


class UltimateFocusLauncher:
    """Ultimate cross-platform Focus Timer launcher"""

    def __init__(self):
        """Initialize the ultimate launcher"""
        self.config_manager = ConfigManager()
        self.music_controller = MusicController(self.config_manager)
        self.notification_manager = NotificationManager(self.config_manager)
        self.session_manager = SessionManager(
            self.config_manager, self.music_controller, self.notification_manager
        )

        # System information
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
        """Check if a Python module is available"""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    def _check_tkinter(self) -> bool:
        """Check if tkinter is available"""
        try:
            import tkinter

            return True
        except ImportError:
            return False

    def print_system_info(self):
        """Print comprehensive system information"""
        print("🚀 Ultimate Focus Timer - System Information")
        print("=" * 50)
        print(
            f"🖥️  Platform: {self.system_info['platform']} ({self.system_info['architecture']})"
        )
        print(f"🐍 Python: {self.system_info['python_version']}")
        print(f"📋 OS Release: {self.system_info['os_release']}")
        print(f"📁 Working Directory: {Path.cwd()}")
        print()

    def print_dependency_status(self):
        """Print dependency status with actionable recommendations"""
        dependencies = self.check_dependencies()

        print("📦 Dependency Status")
        print("=" * 30)

        all_good = True
        for dep, status in dependencies.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {dep.upper()}")
            if not status:
                all_good = False
                self._print_fix_suggestion(dep)

        print()

        if not all_good:
            print("🔧 Fix Issues:")
            print("   Run: python setup.py install")
            print("   Or: python -m pip install -r requirements.txt")
            print()

            if not dependencies.get("mpv", False):
                print("🎵 For music support, install MPV:")
                self._print_mpv_install_instructions()
        else:
            print("🎉 All dependencies satisfied! Ready to focus!")

        print()

    def _print_fix_suggestion(self, dependency: str):
        """Print specific fix suggestions for missing dependencies"""
        suggestions = {
            "tkinter": "   • Install python3-tk (Linux) or use Python from python.org",
            "yaml": "   • pip install PyYAML",
            "plyer": "   • pip install plyer",
            "psutil": "   • pip install psutil",
            "matplotlib": "   • pip install matplotlib",
            "pandas": "   • pip install pandas",
            "mpv": "   • Install MPV media player for music support",
        }

        if dependency in suggestions:
            print(f"      {suggestions[dependency]}")

    def _print_mpv_install_instructions(self):
        """Print platform-specific MPV installation instructions"""
        system = platform.system()

        if system == "Windows":
            print("   Windows: choco install mpv  OR  winget install mpv")
        elif system == "Darwin":  # macOS
            print("   macOS: brew install mpv")
        elif system == "Linux":
            print("   Linux: sudo apt install mpv  OR  sudo pacman -S mpv")
        else:
            print("   Visit: https://mpv.io/installation/")

    def _check_display_available(self) -> bool:
        """Check if a GUI display is available"""
        import os

        # Check for display environment variables
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            return True

        # On Windows, GUI is usually available
        if platform.system() == "Windows":
            return True

        # On macOS, check if we're in a terminal app
        if platform.system() == "Darwin":
            # Basic check - if we're not in SSH, display is likely available
            return not os.environ.get('SSH_CLIENT') and not os.environ.get('SSH_TTY')

        return False

    def launch_gui(self, show_splash: bool = True):
        """Launch the GUI version as a separate process"""
        # Check if GUI display is available
        if not self._check_display_available():
            print("❌ No GUI display available")
            print("💡 You appear to be running in a headless environment (like SSH, Docker, or Codespaces)")
            print("🖥️  GUI mode requires a graphical display")
            print("📋 Available alternatives:")
            print("   • Console mode: python main.py --console")
            print("   • Quick session: python main.py --quick 25")
            print("   • Statistics: python main.py --stats")
            return False

        if show_splash:
            self._show_splash()

        print("🎯 Launching GUI Mode...")
        try:
            # Get the current Python executable and script paths
            python_exe = sys.executable
            gui_script = Path(__file__).parent / "src" / "focus_gui.py"
            working_dir = Path(__file__).parent  # Set working directory to project root

            # Prepare environment variables to ensure proper Python path and Unicode support
            env = os.environ.copy()
            current_pythonpath = env.get("PYTHONPATH", "")
            src_path = str(Path(__file__).parent / "src")
            root_path = str(Path(__file__).parent)

            if current_pythonpath:
                env["PYTHONPATH"] = (
                    f"{root_path}{os.pathsep}{src_path}{os.pathsep}{current_pythonpath}"
                )
            else:
                env["PYTHONPATH"] = f"{root_path}{os.pathsep}{src_path}"

            # Set environment variables for proper Unicode handling
            env["PYTHONIOENCODING"] = "utf-8"
            if platform.system() == "Windows":
                env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

            # Launch GUI as separate process with proper working directory and environment
            if platform.system() == "Windows":
                # On Windows, use CREATE_NEW_PROCESS_GROUP to detach from parent
                process = subprocess.Popen(
                    [python_exe, str(gui_script)],
                    cwd=working_dir,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                # On Unix-like systems, use start_new_session
                process = subprocess.Popen(
                    [python_exe, str(gui_script)],
                    cwd=working_dir,
                    env=env,
                    start_new_session=True,
                )

            # Give the process a moment to start
            time.sleep(2.0)

            # Check if process is still running
            if process.poll() is None:
                print("✅ GUI launched successfully as separate process")
                print("💡 Terminal is now available for other commands")
                return True
            else:
                returncode = process.returncode
                print(f"❌ GUI process exited with code {returncode}")
                if returncode != 0:
                    print("🔧 Falling back to running GUI in current process...")
                    # Fallback to running in current process
                    app = FocusGUI()
                    app.run()
                    return True

        except Exception as e:
            print(f"❌ Error launching GUI: {e}")
            print("💡 Try console mode: python main.py --console")
            print("🔧 Fallback: Running GUI in current process...")
            try:
                # Fallback to running in current process if subprocess fails
                app = FocusGUI()
                app.run()
                return True
            except Exception as fallback_e:
                print(f"❌ Fallback also failed: {fallback_e}")
                return False

    def launch_console(self):
        """Launch the console version"""
        print("💻 Launching Console Mode...")
        try:
            print("   Creating console interface...")
            console = ConsoleInterface()
            print("   Starting console run...")
            console.run()
        except Exception as e:
            import traceback

            print(f"❌ Error launching console: {e}")
            print("📝 Full traceback:")
            traceback.print_exc()
            print("💡 Check dependencies and try again")

    def launch_dashboard(self):
        """Launch the analytics dashboard"""
        print("📊 Launching Analytics Dashboard...")
        try:
            analyzer = SessionAnalyzer()
            dashboard = DashboardGUI(analyzer)

            # Run dashboard (this will block until closed)
            dashboard.run()

            print("📊 Dashboard session completed.")

        except KeyboardInterrupt:
            print("\n📊 Dashboard interrupted by user.")
        except Exception as e:
            import traceback

            print(f"❌ Error launching dashboard: {e}")
            print("📝 Full traceback:")
            traceback.print_exc()
            print("💡 Ensure you have session data to analyze")
        finally:
            print("📊 Returning to launcher...")

    def run_quick_session(self, minutes: int = 25, session_type: str = "work"):
        """Run a quick focus session without GUI"""
        print(f"⚡ Quick {session_type.title()} Session: {minutes} minutes")
        print("=" * 40)

        # Start music if enabled
        if self.config_manager.get("classical_music", True):
            self.music_controller.start_music()

        # Run timer
        try:
            for remaining in range(minutes * 60, 0, -1):
                mins, secs = divmod(remaining, 60)
                print(
                    f"\r⏰ {mins:02d}:{secs:02d} - Stay focused! ", end="", flush=True
                )
                time.sleep(1)

            print("\n🎉 Session completed! Great work!")

            # Log session
            self.session_manager.log_session(session_type, minutes, "completed")

            # Show notification
            self.notification_manager.show_notification(
                "Focus Session Complete!",
                f"{minutes}-minute {session_type} session finished",
            )

        except KeyboardInterrupt:
            print("\n⏸️  Session paused by user")
            self.session_manager.log_session(session_type, minutes, "interrupted")
        finally:
            # Stop music
            self.music_controller.stop_music()

    def show_stats(self):
        """Show quick productivity statistics"""
        print("📈 Productivity Statistics")
        print("=" * 30)

        analyzer = SessionAnalyzer()
        stats = analyzer.get_quick_stats()

        print(f"📅 Today: {stats.get('today_sessions', 0)} sessions")
        print(f"📊 This Week: {stats.get('week_sessions', 0)} sessions")
        print(f"🏆 Total: {stats.get('total_sessions', 0)} sessions")
        print(f"⏱️  Total Time: {stats.get('total_minutes', 0)} minutes")
        print()

        if stats.get("streak", 0) > 0:
            print(f"🔥 Current Streak: {stats['streak']} days")
        else:
            print("💪 Start your productivity streak today!")

    def _show_splash(self):
        """Show animated splash screen"""
        splash_frames = [
            "🎯 Focus Timer Loading    ",
            "🎯 Focus Timer Loading.   ",
            "🎯 Focus Timer Loading..  ",
            "🎯 Focus Timer Loading... ",
        ]

        for _ in range(2):  # Show animation twice
            for frame in splash_frames:
                print(f"\r{frame}", end="", flush=True)
                time.sleep(0.3)

        print("\r🎯 Focus Timer Ready!     ")
        time.sleep(0.5)
        print()

    def interactive_launcher(self):
        """Interactive launcher menu"""
        while True:
            print("\n🎯 Ultimate Focus Timer")
            print("=" * 25)
            print("1. 🖼️  GUI Mode")
            print("2. 💻 Console Mode")
            print("3. 📊 Analytics Dashboard")
            print("4. ⚡ Quick Session (25 min)")
            print("5. ☕ Quick Break (5 min)")
            print("6. 📈 Show Statistics")
            print("7. ⚙️  Check Dependencies")
            print("8. ℹ️  System Information")
            print("9. 🚪 Exit")
            print()

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
                    print("👋 Thanks for using Focus Timer!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Ultimate Focus Timer - Cross-Platform Productivity Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Interactive launcher
  python main.py --gui              # Launch GUI directly
  python main.py --console          # Launch console mode
  python main.py --dashboard        # Open analytics dashboard
  python main.py --quick 25         # 25-minute focus session
  python main.py --break 5          # 5-minute break
  python main.py --stats            # Show statistics
  python main.py --check            # Check dependencies
  python main.py --info             # System information
        """,
    )

    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")
    parser.add_argument("--console", action="store_true", help="Launch console mode")
    parser.add_argument(
        "--dashboard", action="store_true", help="Launch analytics dashboard"
    )
    parser.add_argument(
        "--quick", type=int, metavar="MINUTES", help="Quick focus session"
    )
    parser.add_argument(
        "--break", type=int, metavar="MINUTES", help="Quick break session"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show productivity statistics"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check system dependencies"
    )
    parser.add_argument("--info", action="store_true", help="Show system information")
    parser.add_argument("--no-splash", action="store_true", help="Skip splash screen")

    args = parser.parse_args()

    # Initialize launcher
    launcher = UltimateFocusLauncher()

    # Handle command-line arguments
    if args.info:
        launcher.print_system_info()
    elif args.check:
        launcher.print_dependency_status()
    elif args.stats:
        launcher.show_stats()
    elif args.gui:
        launcher.launch_gui(show_splash=not args.no_splash)
    elif args.console:
        launcher.launch_console()
    elif args.dashboard:
        launcher.launch_dashboard()
    elif args.quick:
        launcher.run_quick_session(args.quick, "work")
    elif getattr(args, "break"):
        launcher.run_quick_session(getattr(args, "break"), "break")
    else:
        # No arguments provided, show interactive launcher
        launcher.interactive_launcher()


if __name__ == "__main__":
    main()
