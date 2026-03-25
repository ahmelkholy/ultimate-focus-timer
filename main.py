#!/usr/bin/env python3
"""
Ultimate Focus Timer - Main Entry Point
"""

import argparse
import logging
import os
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Dict

# ── Bootstrap: make `src` importable when running as a plain script ───────────
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ── Logging must be set up before any src imports so every module gets
#    the configured handlers rather than the default NullHandler. ─────────────
from src.system import setup_logging, ERROR_LOG_FILE, ensure_dirs  # noqa: E402

setup_logging()
logger = logging.getLogger(__name__)

# ── Remaining src imports ─────────────────────────────────────────────────────
from src.core import ConfigManager, SessionManager  # noqa: E402
from src.focus_console import ConsoleInterface  # noqa: E402
from src.system import MusicController, NotificationManager  # noqa: E402

# Ensure runtime directories exist
ensure_dirs()


# ── Global exception handler ──────────────────────────────────────────────────


def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=fh)
            fh.write("\n")
    except OSError:
        pass
    print(f"FATAL ERROR: Details logged to {ERROR_LOG_FILE}")


sys.excepthook = _handle_unhandled_exception


# ── Launcher class ────────────────────────────────────────────────────────────


class UltimateFocusLauncher:
    """Bootstraps and coordinates all top-level application components."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.music_controller = MusicController(self.config_manager)
        self.notification_manager = NotificationManager(self.config_manager)
        # SessionManager is now headless; music/notifications wired via callbacks
        self.session_manager = SessionManager(self.config_manager)
        self.system_info: Dict[str, str] = {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "os_release": platform.release(),
        }
        logger.info(
            "Launcher initialised (platform=%s, python=%s)",
            self.system_info["platform"],
            self.system_info["python_version"],
        )

    # ── Dependency checks ─────────────────────────────────────────────────────

    def check_dependencies(self) -> Dict[str, bool]:
        return {
            "python": sys.version_info >= (3, 8),
            "tkinter": self._check_module("tkinter"),
            "yaml": self._check_module("yaml"),
            "plyer": self._check_module("plyer"),
            "psutil": self._check_module("psutil"),
            "matplotlib": self._check_module("matplotlib"),
            "pandas": self._check_module("pandas"),
            "mpv": self.music_controller.is_mpv_available(),
        }

    def _check_module(self, name: str) -> bool:
        try:
            __import__(name)
            return True
        except ImportError:
            return False

    def print_system_info(self):
        print("--- System Information ---")
        print(
            f"Platform : {self.system_info['platform']} ({self.system_info['architecture']})"
        )
        print(f"Python   : {self.system_info['python_version']}")
        print(f"OS       : {self.system_info['os_release']}")
        print(f"CWD      : {Path.cwd()}")

    def print_dependency_status(self):
        deps = self.check_dependencies()
        print("--- Dependency Status ---")
        for dep, ok in deps.items():
            print(f"{'[V]' if ok else '[X]'} {dep.upper()}")
        if all(deps.values()):
            print("[OK] All dependencies satisfied!")
        else:
            print("Run: pip install -r requirements.txt")

    # ── Launch modes ──────────────────────────────────────────────────────────

    def _check_display_available(self) -> bool:
        if platform.system() == "Windows":
            return True
        if platform.system() == "Darwin":
            return not os.environ.get("SSH_CLIENT") and not os.environ.get("SSH_TTY")
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    def launch_gui(self) -> bool:
        if not self._check_display_available():
            logger.error("No GUI display available; try --console")
            return False
        try:
            from src.ui import FocusGUI

            app = FocusGUI()
            app.run()
            return True
        except Exception:
            logger.exception("Error launching GUI")
            return False

    def launch_console(self):
        logger.info("Launching console mode")
        try:
            console = ConsoleInterface()
            console.run()
        except Exception:
            logger.exception("Error launching console")

    def launch_dashboard(self):
        logger.info("Launching analytics dashboard")
        try:
            from src.ui import DashboardGUI, SessionAnalyzer

            analyzer = SessionAnalyzer()
            DashboardGUI(analyzer).run()
        except ImportError:
            print("[X] Dashboard requires: pip install matplotlib pandas")
        except KeyboardInterrupt:
            print("\nDashboard interrupted.")
        except Exception:
            logger.exception("Error launching dashboard")

    def run_quick_session(self, minutes: int = 25, session_type: str = "work"):
        logger.info("Quick %s session: %d minutes", session_type, minutes)
        if self.config_manager.get("classical_music", True):
            self.music_controller.start_music()
        try:
            for remaining in range(minutes * 60, 0, -1):
                mins, secs = divmod(remaining, 60)
                print(
                    f"\rTime: {mins:02d}:{secs:02d} - Stay focused!", end="", flush=True
                )
                time.sleep(1)
            print("\n[OK] Session completed!")
            self.session_manager.log_session(session_type, minutes, "completed")
            self.notification_manager.show_notification(
                "Focus Session Complete!",
                f"{minutes}-minute {session_type} session finished.",
            )
        except KeyboardInterrupt:
            print("\n[!] Session interrupted.")
            self.session_manager.log_session(session_type, minutes, "interrupted")
        finally:
            self.music_controller.stop_music()

    def show_stats(self):
        try:
            from src.ui import SessionAnalyzer

            stats = SessionAnalyzer().get_quick_stats()
            print(f"Today   : {stats.get('today_sessions', 0)} sessions")
            print(f"Week    : {stats.get('week_sessions', 0)} sessions")
            print(
                f"Total   : {stats.get('total_sessions', 0)} sessions "
                f"({stats.get('total_minutes', 0)} min)"
            )
        except ImportError:
            print("[X] Dashboard requires: pip install matplotlib pandas")

    # ── Interactive text launcher ─────────────────────────────────────────────

    def interactive_launcher(self):
        while True:
            print("\n--- Ultimate Focus Timer ---")
            print("1. GUI  2. Console  3. Dashboard  4. Quick Work (25m)")
            print("5. Quick Break (5m)  6. Stats  7. Deps  8. Sys Info  9. Exit")
            try:
                choice = input("Choose (1-9): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break

            dispatch = {
                "1": self.launch_gui,
                "2": self.launch_console,
                "3": self.launch_dashboard,
                "4": lambda: self.run_quick_session(25, "work"),
                "5": lambda: self.run_quick_session(5, "break"),
                "6": self.show_stats,
                "7": self.print_dependency_status,
                "8": self.print_system_info,
                "9": None,
            }
            if choice == "9":
                print("Goodbye!")
                break
            action = dispatch.get(choice)
            if action:
                try:
                    action()
                except Exception:
                    logger.exception("Error in interactive launcher")
            elif choice:
                print("[!] Invalid choice.")


# ── CLI entry point ───────────────────────────────────────────────────────────


def _detach_gui_on_windows() -> None:
    """Re-launch under pythonw.exe so the terminal window disappears immediately.

    Only runs on Windows and only when we are currently attached to a console
    (i.e. sys.executable is python.exe, not pythonw.exe).  The child inherits
    no standard handles, so the parent terminal is free the moment this returns.
    """
    if platform.system() != "Windows":
        return
    exe = Path(sys.executable)
    if exe.name.lower() == "pythonw.exe":
        return  # already detached

    pythonw = exe.parent / "pythonw.exe"
    if not pythonw.exists():
        return  # pythonw not found — fall back to attached mode

    subprocess.Popen(
        [str(pythonw)] + sys.argv,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)


def _create_desktop_shortcut() -> None:
    """Create a Desktop shortcut pointing to focus.pyw (Windows only)."""
    if platform.system() != "Windows":
        print("[!] --install is only supported on Windows.")
        return

    from src.system import PROJECT_ROOT  # noqa: E402

    target = PROJECT_ROOT / "focus.pyw"
    if not target.exists():
        print(f"[X] Launcher not found: {target}")
        return

    desktop = Path.home() / "Desktop"
    shortcut = desktop / "Focus Timer.lnk"

    # Use Windows Script Host via a temporary VBScript
    vbs_content = f"""\
Set WshShell = WScript.CreateObject("WScript.Shell")
Set oLink = WshShell.CreateShortcut("{shortcut}")
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{PROJECT_ROOT}"
oLink.Description = "Ultimate Focus Timer"
oLink.Save
"""
    import tempfile

    with tempfile.NamedTemporaryFile(
        suffix=".vbs", delete=False, mode="w", encoding="utf-8"
    ) as fh:
        fh.write(vbs_content)
        vbs_path = fh.name

    try:
        result = subprocess.run(
            ["cscript", "//NoLogo", vbs_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print(f"[OK] Desktop shortcut created: {shortcut}")
        else:
            print(f"[X] Failed to create shortcut: {result.stderr.strip()}")
    except FileNotFoundError:
        print("[X] cscript not found — cannot create shortcut.")
    except Exception as exc:
        print(f"[X] Error creating shortcut: {exc}")
    finally:
        Path(vbs_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Ultimate Focus Timer")
    parser.add_argument("--gui", action="store_true", help="Launch GUI mode")
    parser.add_argument("--console", action="store_true", help="Launch console mode")
    parser.add_argument(
        "--dashboard", action="store_true", help="Launch analytics dashboard"
    )
    parser.add_argument("--quick-session", type=int, metavar="MINUTES")
    parser.add_argument("--quick-break", type=int, metavar="MINUTES")
    parser.add_argument("--stats", action="store_true")
    parser.add_argument("--check-deps", action="store_true")
    parser.add_argument("--sys-info", action="store_true")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Create a Desktop shortcut to the app (Windows)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG logging to console"
    )
    args = parser.parse_args()

    if args.verbose:
        setup_logging(verbose=True)

    # Detach from the terminal console on Windows as early as possible so the
    # command prompt is not blocked for the entire GUI session.
    if args.gui:
        _detach_gui_on_windows()

    if args.install:
        _create_desktop_shortcut()
        return

    launcher = UltimateFocusLauncher()

    if args.gui:
        launcher.launch_gui()
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
        launcher.interactive_launcher()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
