#!/usr/bin/env python3
"""
Focus Application Launcher
Main entry point for the Focus Timer application with GUI/Console mode selection
"""

import argparse
import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk, messagebox

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_manager import ConfigManager
    from focus_gui import FocusTimerGUI
    from focus_console import ConsoleInterface
    from dashboard import DashboardGUI, SessionAnalyzer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required files are present and dependencies are installed.")
    sys.exit(1)


class LauncherGUI:
    """GUI launcher for selecting application mode"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Focus Timer Launcher")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#2c3e50')

        # Center window
        self.center_window()

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.create_widgets()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")

    def configure_styles(self):
        """Configure custom styles"""
        self.style.configure('Title.TLabel',
                           font=('Arial', 24, 'bold'),
                           background='#2c3e50',
                           foreground='#ecf0f1')

        self.style.configure('Subtitle.TLabel',
                           font=('Arial', 12),
                           background='#2c3e50',
                           foreground='#bdc3c7')

        self.style.configure('Launch.TButton',
                           font=('Arial', 14, 'bold'),
                           padding=(20, 15))

        self.style.configure('Option.TButton',
                           font=('Arial', 11),
                           padding=(15, 10))

        self.style.configure('Card.TFrame',
                           background='#34495e',
                           relief='raised',
                           borderwidth=2)

    def create_widgets(self):
        """Create and layout widgets"""
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=120)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(header_frame, text="🎯 FOCUS TIMER", style='Title.TLabel')
        title_label.pack(pady=(20, 5))

        subtitle_label = ttk.Label(header_frame,
                                  text="Boost your productivity with the Pomodoro Technique",
                                  style='Subtitle.TLabel')
        subtitle_label.pack()

        # Main content
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Launch options
        options_frame = ttk.Frame(content_frame, style='Card.TFrame')
        options_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Option 1: GUI Timer
        gui_frame = tk.Frame(options_frame, bg='#34495e')
        gui_frame.pack(fill='x', padx=20, pady=(20, 10))

        gui_icon = tk.Label(gui_frame, text="🖥️", font=('Arial', 32), bg='#34495e', fg='#3498db')
        gui_icon.pack(side='left', padx=(0, 15))

        gui_info = tk.Frame(gui_frame, bg='#34495e')
        gui_info.pack(side='left', fill='both', expand=True)

        gui_title = tk.Label(gui_info, text="GUI Timer", font=('Arial', 16, 'bold'),
                            bg='#34495e', fg='white')
        gui_title.pack(anchor='w')

        gui_desc = tk.Label(gui_info, text="Modern graphical interface with progress bars,\nstatistics, and easy session management",
                           font=('Arial', 10), bg='#34495e', fg='#bdc3c7')
        gui_desc.pack(anchor='w')

        gui_button = ttk.Button(gui_frame, text="Launch GUI", style='Launch.TButton',
                               command=self.launch_gui)
        gui_button.pack(side='right', padx=(10, 0))

        # Separator
        separator1 = ttk.Separator(options_frame, orient='horizontal')
        separator1.pack(fill='x', padx=20, pady=10)

        # Option 2: Console Timer
        console_frame = tk.Frame(options_frame, bg='#34495e')
        console_frame.pack(fill='x', padx=20, pady=10)

        console_icon = tk.Label(console_frame, text="⌨️", font=('Arial', 32), bg='#34495e', fg='#2ecc71')
        console_icon.pack(side='left', padx=(0, 15))

        console_info = tk.Frame(console_frame, bg='#34495e')
        console_info.pack(side='left', fill='both', expand=True)

        console_title = tk.Label(console_info, text="Console Timer", font=('Arial', 16, 'bold'),
                                bg='#34495e', fg='white')
        console_title.pack(anchor='w')

        console_desc = tk.Label(console_info, text="Terminal-based interface for keyboard enthusiasts\nand minimal resource usage",
                               font=('Arial', 10), bg='#34495e', fg='#bdc3c7')
        console_desc.pack(anchor='w')

        console_button = ttk.Button(console_frame, text="Launch Console", style='Launch.TButton',
                                   command=self.launch_console)
        console_button.pack(side='right', padx=(10, 0))

        # Separator
        separator2 = ttk.Separator(options_frame, orient='horizontal')
        separator2.pack(fill='x', padx=20, pady=10)

        # Option 3: Analytics Dashboard
        dashboard_frame = tk.Frame(options_frame, bg='#34495e')
        dashboard_frame.pack(fill='x', padx=20, pady=10)

        dashboard_icon = tk.Label(dashboard_frame, text="📊", font=('Arial', 32), bg='#34495e', fg='#e74c3c')
        dashboard_icon.pack(side='left', padx=(0, 15))

        dashboard_info = tk.Frame(dashboard_frame, bg='#34495e')
        dashboard_info.pack(side='left', fill='both', expand=True)

        dashboard_title = tk.Label(dashboard_info, text="Analytics Dashboard", font=('Arial', 16, 'bold'),
                                  bg='#34495e', fg='white')
        dashboard_title.pack(anchor='w')

        dashboard_desc = tk.Label(dashboard_info, text="Detailed productivity analytics with charts,\ninsights, and session history",
                                 font=('Arial', 10), bg='#34495e', fg='#bdc3c7')
        dashboard_desc.pack(anchor='w')

        dashboard_button = ttk.Button(dashboard_frame, text="View Analytics", style='Launch.TButton',
                                     command=self.launch_dashboard)
        dashboard_button.pack(side='right', padx=(10, 0))

        # Bottom section
        bottom_frame = tk.Frame(content_frame, bg='#2c3e50')
        bottom_frame.pack(fill='x', pady=(20, 0))

        # Utility buttons
        utils_frame = tk.Frame(bottom_frame, bg='#2c3e50')
        utils_frame.pack(fill='x')

        ttk.Button(utils_frame, text="⚙️ Configuration", style='Option.TButton',
                  command=self.open_config).pack(side='left', padx=(0, 10))

        ttk.Button(utils_frame, text="📁 Open Data Folder", style='Option.TButton',
                  command=self.open_data_folder).pack(side='left', padx=(0, 10))

        ttk.Button(utils_frame, text="🆘 Help", style='Option.TButton',
                  command=self.show_help).pack(side='left', padx=(0, 10))

        ttk.Button(utils_frame, text="❌ Exit", style='Option.TButton',
                  command=self.root.quit).pack(side='right')

        # Status bar
        status_frame = tk.Frame(bottom_frame, bg='#2c3e50', height=30)
        status_frame.pack(fill='x', pady=(10, 0))
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="Ready to focus! Select an option above to begin.",
                                   font=('Arial', 9), bg='#2c3e50', fg='#95a5a6')
        self.status_label.pack(side='left', pady=5)

        version_label = tk.Label(status_frame, text="v2.0 Python Edition",
                               font=('Arial', 9), bg='#2c3e50', fg='#95a5a6')
        version_label.pack(side='right', pady=5)

    def update_status(self, message: str):
        """Update status message"""
        self.status_label.config(text=message)
        self.root.update()

    def launch_gui(self):
        """Launch the GUI timer"""
        try:
            self.update_status("Launching GUI Timer...")
            self.root.withdraw()  # Hide launcher

            # Create and run GUI
            config = ConfigManager()
            gui = FocusTimerGUI(config)
            gui.run()

            # Show launcher again when GUI closes
            self.root.deiconify()
            self.update_status("GUI Timer closed. Ready for next session!")

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch GUI Timer:\n{str(e)}")
            self.update_status("Error launching GUI Timer")

    def launch_console(self):
        """Launch the console timer"""
        try:
            self.update_status("Launching Console Timer...")

            # Launch in new terminal/command prompt
            python_exe = sys.executable
            script_path = Path(__file__).parent / "focus_console.py"

            if os.name == 'nt':  # Windows
                subprocess.Popen([
                    'cmd', '/c', 'start', 'cmd', '/k',
                    f'"{python_exe}" "{script_path}" --interactive'
                ])
            elif os.name == 'posix':  # macOS/Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.Popen([
                        'osascript', '-e',
                        f'tell application "Terminal" to do script "{python_exe} {script_path} --interactive"'
                    ])
                else:  # Linux
                    # Try different terminal emulators
                    terminals = ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal']
                    for terminal in terminals:
                        try:
                            subprocess.Popen([terminal, '-e', f'{python_exe} {script_path} --interactive'])
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        # Fallback: run in current terminal
                        subprocess.Popen([python_exe, str(script_path), '--interactive'])

            self.update_status("Console Timer launched in new terminal")

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch Console Timer:\n{str(e)}")
            self.update_status("Error launching Console Timer")

    def launch_dashboard(self):
        """Launch the analytics dashboard"""
        try:
            self.update_status("Loading Analytics Dashboard...")

            # Create and run dashboard
            analyzer = SessionAnalyzer()
            dashboard = DashboardGUI(analyzer)
            dashboard.run()

            self.update_status("Analytics Dashboard closed")

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch Analytics Dashboard:\n{str(e)}")
            self.update_status("Error launching Analytics Dashboard")

    def open_config(self):
        """Open configuration file"""
        try:
            config = ConfigManager()
            config_path = config.config_path

            if config_path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(config_path))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(config_path)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(config_path)])

                self.update_status(f"Opened configuration file: {config_path}")
            else:
                messagebox.showwarning("File Not Found", "Configuration file not found!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open configuration:\n{str(e)}")

    def open_data_folder(self):
        """Open the data folder"""
        try:
            config = ConfigManager()
            data_path = config.get_app_config()['data_path']
            data_dir = Path(data_path).parent

            if data_dir.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(data_dir))
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(data_dir)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(data_dir)])

                self.update_status(f"Opened data folder: {data_dir}")
            else:
                messagebox.showwarning("Folder Not Found", "Data folder not found!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open data folder:\n{str(e)}")

    def show_help(self):
        """Show help information"""
        help_text = """🎯 FOCUS TIMER HELP

WHAT IS FOCUS TIMER?
Focus Timer is a productivity application based on the Pomodoro Technique:
• Work in focused 25-minute sessions
• Take short 5-minute breaks between sessions
• Take longer 15-30 minute breaks every 4 sessions
• Classical music helps maintain concentration

AVAILABLE MODES:

🖥️ GUI Timer
• Visual interface with progress bars
• Real-time statistics and session tracking
• Easy-to-use controls and settings
• Perfect for desktop users

⌨️ Console Timer
• Terminal-based interface
• Minimal resource usage
• Keyboard shortcuts and commands
• Great for developers and CLI enthusiasts

📊 Analytics Dashboard
• Detailed productivity insights
• Charts and visualizations
• Export capabilities
• Track your progress over time

FEATURES:
• Cross-platform compatibility (Windows, macOS, Linux)
• Classical music integration with MPV player
• Smart notifications and system tray integration
• Comprehensive session logging and analytics
• Flexible configuration options
• Auto-start sessions and breaks

GETTING STARTED:
1. Choose your preferred interface (GUI or Console)
2. Configure your session durations if needed
3. Start your first work session
4. Take breaks when prompted
5. Review your progress in the Analytics Dashboard

For more help, visit the configuration file or check the documentation.
"""

        # Create help window
        help_window = tk.Toplevel(self.root)
        help_window.title("🆘 Focus Timer Help")
        help_window.geometry("600x700")
        help_window.resizable(True, True)
        help_window.configure(bg='#2c3e50')

        # Text widget with scrollbar
        text_frame = tk.Frame(help_window, bg='#2c3e50')
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)

        text_widget = tk.Text(text_frame, wrap='word', bg='#34495e', fg='white',
                             font=('Consolas', 11), padx=15, pady=15)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')

        # Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)

    def run(self):
        """Start the launcher GUI"""
        self.root.mainloop()


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []

    try:
        import yaml
    except ImportError:
        missing_deps.append("PyYAML")

    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")

    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")

    try:
        import seaborn
    except ImportError:
        missing_deps.append("seaborn")

    try:
        import plyer
    except ImportError:
        missing_deps.append("plyer")

    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n📦 Install missing dependencies with:")
        print(f"   pip install {' '.join(missing_deps)}")
        print("\n   Or install all requirements:")
        print("   pip install -r requirements.txt")
        return False

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Focus Timer Application Launcher")

    # Mode selection
    parser.add_argument('--gui', action='store_true', help='Launch GUI timer directly')
    parser.add_argument('--console', action='store_true', help='Launch console timer directly')
    parser.add_argument('--dashboard', action='store_true', help='Launch analytics dashboard directly')
    parser.add_argument('--launcher', action='store_true', help='Show launcher GUI (default)')

    # Quick start options
    parser.add_argument('--work', type=int, metavar='MINUTES',
                       help='Start a work session for specified minutes (console mode)')
    parser.add_argument('--break', type=int, metavar='MINUTES',
                       help='Start a break session for specified minutes (console mode)')
    parser.add_argument('--pomodoro', action='store_true',
                       help='Start a standard 25-minute Pomodoro session (console mode)')

    # Configuration
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies and exit')

    args = parser.parse_args()

    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("✅ All dependencies are available!")
        sys.exit(0)

    # Verify dependencies before launching
    if not check_dependencies():
        sys.exit(1)

    try:
        # Handle quick start options
        if args.work or args.break or args.pomodoro:
            console = ConsoleInterface(args.config)
            if args.work:
                console.run_command('start', args.work, 'work')
            elif args.break:
                console.run_command('start', args.break, 'short_break')
            elif args.pomodoro:
                console.run_command('start', 25, 'work')

        # Handle direct mode launches
        elif args.gui:
            config = ConfigManager(args.config)
            gui = FocusTimerGUI(config)
            gui.run()

        elif args.console:
            console = ConsoleInterface(args.config)
            console.run_interactive()

        elif args.dashboard:
            analyzer = SessionAnalyzer()
            dashboard = DashboardGUI(analyzer)
            dashboard.run()

        else:
            # Default to launcher GUI
            launcher = LauncherGUI()
            launcher.run()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
