#!/usr/bin/env python3
"""
Ultimate Focus Timer - Cross-Platform Productivity Application
Main entry point with comprehensive functionality and cross-platform support
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

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


# --- Main Application ---
from config_manager import ConfigManager
from focus_console import ConsoleInterface


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

    args = parser.parse_args()

    if args.gui:
        from src.focus_gui import FocusGUI

        gui = FocusGUI()
        gui.run()
        return

    # --- Configuration Management ---
    config_manager = ConfigManager("config.json")
    config = config_manager.load_config()

    # --- Session Management ---
    session_manager = SessionManager(config["session_length"], config["break_length"])
    session_data = session_manager.load_session_data()

    # --- Focus Console Interface ---
    console_interface = ConsoleInterface(session_manager, config["console_width"])
    console_interface.display_welcome()

    try:
        while True:
            # --- Main Application Loop ---
            console_interface.display_menu()
            choice = console_interface.get_user_choice()

            if choice == "1":
                # Start session
                session_manager.start_session()
            elif choice == "2":
                # View session report
                console_interface.display_session_report(session_data)
            elif choice == "3":
                # Configure settings
                config_manager.configure_settings()
            elif choice == "4":
                # Exit application
                console_interface.exit_application()
                break
            else:
                console_interface.display_error("Invalid choice. Please try again.")

    except Exception as e:
        log_error(sys.exc_info())
        console_interface.display_error(f"An unexpected error occurred: {str(e)}")

    finally:
        # --- Cleanup ---
        session_manager.save_session_data(session_data)
        console_interface.display_goodbye()


if __name__ == "__main__":
    main()
