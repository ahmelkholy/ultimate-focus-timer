#!/usr/bin/env python3
"""
GUI Focus Timer for Enhanced Focus Timer
Cross-platform GUI using tkinter with modern styling
"""

import tkinter as tk
from tkinter import messagebox, ttk

from config_manager import ConfigManager
from music_controller import MusicController
from notification_manager import NotificationManager
from session_manager import SessionManager, SessionState, SessionType


class FocusGUI:
    """Modern GUI for the Focus Timer application"""

    def __init__(self):
        """Initialize the GUI application"""
        # Initialize components
        self.config = ConfigManager()
        self.music = MusicController(self.config)
        self.notifications = NotificationManager(self.config)
        self.session_manager = SessionManager(
            self.config, self.music, self.notifications
        )

        # Set up session callbacks
        self.session_manager.set_callbacks(
            on_tick=self.on_session_tick,
            on_complete=self.on_session_complete,
            on_state_change=self.on_session_state_change,
        )

        # GUI setup
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.apply_theme()
        self.update_display()

        # Start update loop
        self.root.after(100, self.update_loop)

    def setup_window(self):
        """Configure the main window"""
        self.root.title("🎯 Enhanced Focus Timer")
        self.root.geometry("380x520")
        self.root.resizable(False, False)

        # Configure grid weights for proper expansion
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (380 // 2)
        y = (self.root.winfo_screenheight() // 2) - (520 // 2)
        self.root.geometry(f"380x520+{x}+{y}")

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="8")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main frame grid weights for equal distribution
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        # Title
        self.title_label = ttk.Label(
            self.main_frame, text="🎯 FOCUS TIMER", font=("Arial", 18, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=3, pady=(0, 12))

        # Session type label
        self.session_type_label = ttk.Label(
            self.main_frame, text="READY TO START", font=("Arial", 11, "bold")
        )
        self.session_type_label.grid(row=1, column=0, columnspan=3, pady=(0, 8))

        # Time display
        self.time_label = ttk.Label(
            self.main_frame, text="00:00", font=("Courier New", 42, "bold")
        )
        self.time_label.grid(row=2, column=0, columnspan=3, pady=(0, 15))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.main_frame, variable=self.progress_var, maximum=100, length=300
        )
        self.progress_bar.grid(
            row=3, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E), padx=8
        )

        # Session buttons frame
        self.session_frame = ttk.Frame(self.main_frame)
        self.session_frame.grid(row=4, column=0, columnspan=3, pady=(0, 15))

        # Session buttons
        self.work_button = ttk.Button(
            self.session_frame,
            text=f"Work Session ({self.config.get('work_mins')} min)",
            command=lambda: self.start_session(SessionType.WORK),
            width=18,
        )
        self.work_button.grid(row=0, column=0, padx=3, pady=3)

        self.short_break_button = ttk.Button(
            self.session_frame,
            text=f"Short Break ({self.config.get('short_break_mins')} min)",
            command=lambda: self.start_session(SessionType.SHORT_BREAK),
            width=18,
        )
        self.short_break_button.grid(row=0, column=1, padx=3, pady=3)

        self.long_break_button = ttk.Button(
            self.session_frame,
            text=f"Long Break ({self.config.get('long_break_mins')} min)",
            command=lambda: self.start_session(SessionType.LONG_BREAK),
            width=18,
        )
        self.long_break_button.grid(row=1, column=0, padx=3, pady=3)

        self.custom_button = ttk.Button(
            self.session_frame,
            text="Custom Session",
            command=self.start_custom_session,
            width=18,
        )
        self.custom_button.grid(row=1, column=1, padx=3, pady=3)

        # Control buttons frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=5, column=0, columnspan=3, pady=(0, 15))

        # Control buttons
        self.pause_button = ttk.Button(
            self.control_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            state="disabled",
            width=11,
        )
        self.pause_button.grid(row=0, column=0, padx=3)

        self.stop_button = ttk.Button(
            self.control_frame,
            text="⏹ Stop",
            command=self.stop_session,
            state="disabled",
            width=11,
        )
        self.stop_button.grid(row=0, column=1, padx=3)

        self.music_button = ttk.Button(
            self.control_frame, text="🎵 Music", command=self.toggle_music, width=11
        )
        self.music_button.grid(row=0, column=2, padx=3)

        # Status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(row=6, column=0, columnspan=3, pady=(0, 8))

        # Status labels
        self.music_status_label = ttk.Label(
            self.status_frame, text="♪ Music Ready", font=("Arial", 8)
        )
        self.music_status_label.grid(row=0, column=0, padx=8)

        self.session_count_label = ttk.Label(
            self.status_frame, text="Sessions: 0", font=("Arial", 8)
        )
        self.session_count_label.grid(row=0, column=1, padx=8)

        # Additional buttons frame
        self.additional_frame = ttk.Frame(self.main_frame)
        self.additional_frame.grid(row=7, column=0, columnspan=3)

        # Additional buttons
        self.stats_button = ttk.Button(
            self.additional_frame,
            text="📊 Statistics",
            command=self.show_statistics,
            width=13,
        )
        self.stats_button.grid(row=0, column=0, padx=3, pady=3)

        self.settings_button = ttk.Button(
            self.additional_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            width=13,
        )
        self.settings_button.grid(row=0, column=1, padx=3, pady=3)

        self.test_button = ttk.Button(
            self.additional_frame,
            text="🧪 Test Music",
            command=self.test_music,
            width=13,
        )
        self.test_button.grid(row=0, column=2, padx=3, pady=3)

    def apply_theme(self):
        """Apply dark theme if enabled"""
        if self.config.get("dark_theme", True):
            # Configure dark theme colors
            style = ttk.Style()

            # Use a dark theme if available
            try:
                style.theme_use("clam")

                # Configure colors
                bg_color = "#2b2b2b"
                fg_color = "#ffffff"
                select_color = "#404040"
                accent_color = self.config.get("accent_color", "#00ff00")

                style.configure("TLabel", background=bg_color, foreground=fg_color)
                style.configure("TButton", background=select_color, foreground=fg_color)
                style.configure("TFrame", background=bg_color)
                style.configure("TProgressbar", background=accent_color)

                self.root.configure(bg=bg_color)

            except tk.TclError:
                pass  # Fall back to default theme

    def start_session(self, session_type: SessionType):
        """Start a session of the specified type"""
        self.session_manager.start_session(session_type)
        self.update_button_states()

    def start_custom_session(self):
        """Start a custom duration session"""
        dialog = CustomSessionDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            session_type, duration = dialog.result
            self.session_manager.start_session(session_type, duration)
            self.update_button_states()

    def toggle_pause(self):
        """Toggle pause/resume for current session"""
        if self.session_manager.state == SessionState.RUNNING:
            self.session_manager.pause_session()
        elif self.session_manager.state == SessionState.PAUSED:
            self.session_manager.resume_session()

        self.update_button_states()

    def stop_session(self):
        """Stop the current session"""
        result = messagebox.askyesno(
            "Stop Session", "Are you sure you want to stop the current session?"
        )

        if result:
            self.session_manager.stop_session()
            self.update_button_states()

    def toggle_music(self):
        """Toggle music on/off"""
        if self.music.is_playing:
            self.music.stop_music()
            self.music_status_label.config(text="♪ Music Stopped")
        else:
            if self.music.start_music():
                self.music_status_label.config(text="♪ Music Playing")
            else:
                self.music_status_label.config(text="♪ Music Error")

    def test_music(self):
        """Test music functionality"""
        if not self.music.is_mpv_available():
            messagebox.showerror(
                "Music Test",
                "MPV is not available. Please install MPV for music support.\n\n"
                "Visit: https://mpv.io/ for installation instructions.",
            )
            return

        result = messagebox.askyesno(
            "Music Test", "Test classical music for 5 seconds?"
        )

        if result:
            self.music.start_music(volume=20)
            self.root.after(5000, lambda: self.music.stop_music())
            self.music_status_label.config(text="♪ Testing Music...")
            self.root.after(
                5500, lambda: self.music_status_label.config(text="♪ Test Complete")
            )

    def show_statistics(self):
        """Show session statistics"""
        stats = self.session_manager.get_session_statistics()

        stats_text = f"""Session Statistics:

Total Sessions: {stats['total_sessions']}
Work Sessions: {stats['work_sessions']}
Break Sessions: {stats['break_sessions']}

Total Work Time: {stats['total_work_time']:.1f} minutes
Total Break Time: {stats['total_break_time']:.1f} minutes

Average Work Session: {stats['average_work_session']:.1f} minutes
Average Break Session: {stats['average_break_session']:.1f} minutes

Today's Sessions: {stats['today_sessions']}
Today's Work Time: {stats['today_work_time']:.1f} minutes"""

        messagebox.showinfo("Session Statistics", stats_text)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.root, self.config)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            # Reload configuration
            self.config.load_config()
            # Update button labels
            self.work_button.config(
                text=f"Work Session ({self.config.get('work_mins')} min)"
            )
            self.short_break_button.config(
                text=f"Short Break ({self.config.get('short_break_mins')} min)"
            )
            self.long_break_button.config(
                text=f"Long Break ({self.config.get('long_break_mins')} min)"
            )

    def on_session_tick(self, elapsed_seconds: int, total_seconds: int):
        """Handle session timer tick"""
        # This will be called from update_loop to avoid threading issues
        pass

    def on_session_complete(self, session_type: SessionType, duration: int):
        """Handle session completion"""
        self.root.after_idle(self.update_display)
        self.root.after_idle(self.update_button_states)

        # Show completion dialog
        self.root.after_idle(
            lambda: self.show_completion_dialog(session_type, duration)
        )

    def on_session_state_change(self, old_state: SessionState, new_state: SessionState):
        """Handle session state changes"""
        self.root.after_idle(self.update_display)
        self.root.after_idle(self.update_button_states)

    def show_completion_dialog(self, session_type: SessionType, duration: int):
        """Show session completion dialog"""
        session_name = session_type.value.replace("_", " ").title()

        # Suggest next session
        if session_type == SessionType.WORK:
            completed_work = self.session_manager.completed_work_sessions
            if completed_work % self.config.get("long_break_interval", 4) == 0:
                next_session = "Long Break"
                next_type = SessionType.LONG_BREAK
            else:
                next_session = "Short Break"
                next_type = SessionType.SHORT_BREAK
        else:
            next_session = "Work Session"
            next_type = SessionType.WORK

        result = messagebox.askyesno(
            "Session Complete! 🎉",
            f"Excellent work! You completed a {duration}-minute {session_name}.\n\n"
            f"Would you like to start a {next_session} now?",
        )

        if result:
            self.start_session(next_type)

    def update_display(self):
        """Update the display with current session info"""
        info = self.session_manager.get_session_info()

        # Update session type label
        if info["state"] == "ready":
            self.session_type_label.config(text="READY TO START")
        elif info["state"] == "running":
            session_name = info["type"].replace("_", " ").upper()
            self.session_type_label.config(text=f"{session_name} SESSION")
        elif info["state"] == "paused":
            session_name = info["type"].replace("_", " ").upper()
            self.session_type_label.config(text=f"{session_name} PAUSED")
        elif info["state"] == "completed":
            self.session_type_label.config(text="SESSION COMPLETE!")
        elif info["state"] == "stopped":
            self.session_type_label.config(text="SESSION STOPPED")

        # Update time display
        if info["state"] in ["ready", "stopped"]:
            self.time_label.config(text="00:00")
        elif info["state"] == "completed":
            self.time_label.config(text="COMPLETE!")
        else:
            time_text = self.session_manager.get_time_display()
            self.time_label.config(text=time_text)

        # Update progress bar
        self.progress_var.set(info["progress_percent"])

        # Update session counter
        self.session_count_label.config(text=f"Sessions: {info['session_count']}")

        # Update music status
        music_status = self.music.get_status()
        if music_status["is_playing"]:
            self.music_status_label.config(text="♪ Music Playing")
        else:
            self.music_status_label.config(text="♪ Music Ready")

    def update_button_states(self):
        """Update button states based on session state"""
        state = self.session_manager.state

        # Session buttons
        session_buttons = [
            self.work_button,
            self.short_break_button,
            self.long_break_button,
            self.custom_button,
        ]

        if state == SessionState.READY:
            for btn in session_buttons:
                btn.config(state="normal")
            self.pause_button.config(state="disabled", text="⏸ Pause")
            self.stop_button.config(state="disabled")

        elif state == SessionState.RUNNING:
            for btn in session_buttons:
                btn.config(state="disabled")
            self.pause_button.config(state="normal", text="⏸ Pause")
            self.stop_button.config(state="normal")

        elif state == SessionState.PAUSED:
            for btn in session_buttons:
                btn.config(state="disabled")
            self.pause_button.config(state="normal", text="▶ Resume")
            self.stop_button.config(state="normal")

        elif state in [SessionState.COMPLETED, SessionState.STOPPED]:
            for btn in session_buttons:
                btn.config(state="normal")
            self.pause_button.config(state="disabled", text="⏸ Pause")
            self.stop_button.config(state="disabled")

    def update_loop(self):
        """Main update loop for GUI"""
        self.update_display()
        self.root.after(1000, self.update_loop)  # Update every second

    def on_closing(self):
        """Handle application closing"""
        if self.session_manager.state in [SessionState.RUNNING, SessionState.PAUSED]:
            result = messagebox.askyesno(
                "Close Application",
                "A session is currently active. Stop the session and close?",
            )

            if result:
                self.session_manager.cleanup()
                self.music.cleanup()
                self.root.destroy()
        else:
            self.session_manager.cleanup()
            self.music.cleanup()
            self.root.destroy()

    def run(self):
        """Start the GUI application"""
        print("🎯 Starting Enhanced Focus Timer GUI...")
        self.root.mainloop()


class CustomSessionDialog:
    """Dialog for creating custom duration sessions"""

    def __init__(self, parent):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Custom Session")
        self.dialog.geometry("300x200")
        self.dialog.resizable(False, False)

        # Center on parent
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Main frame
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Session type
        ttk.Label(frame, text="Session Type:").pack(pady=5)
        self.type_var = tk.StringVar(value="work")
        type_frame = ttk.Frame(frame)
        type_frame.pack(pady=5)

        ttk.Radiobutton(
            type_frame, text="Work", variable=self.type_var, value="work"
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            type_frame, text="Break", variable=self.type_var, value="break"
        ).pack(side=tk.LEFT, padx=10)

        # Duration
        ttk.Label(frame, text="Duration (minutes):").pack(pady=(20, 5))
        self.duration_var = tk.StringVar(value="25")
        duration_entry = ttk.Entry(frame, textvariable=self.duration_var, width=10)
        duration_entry.pack(pady=5)
        duration_entry.focus()

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Start", command=self.ok_clicked).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(
            side=tk.LEFT, padx=5
        )

        # Enter key binding
        self.dialog.bind("<Return>", lambda e: self.ok_clicked())
        self.dialog.bind("<Escape>", lambda e: self.cancel_clicked())

    def ok_clicked(self):
        try:
            duration = int(self.duration_var.get())
            if duration <= 0:
                raise ValueError("Duration must be positive")

            session_type = (
                SessionType.WORK
                if self.type_var.get() == "work"
                else SessionType.SHORT_BREAK
            )
            self.result = (session_type, duration)
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please enter a valid positive number for duration."
            )

    def cancel_clicked(self):
        self.dialog.destroy()


class SettingsDialog:
    """Dialog for application settings"""

    def __init__(self, parent, config_manager):
        self.config = config_manager
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)

        # Center on parent
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Session settings tab
        session_frame = ttk.Frame(notebook, padding="10")
        notebook.add(session_frame, text="Sessions")

        # Work duration
        ttk.Label(session_frame, text="Work Session (minutes):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.work_mins_var = tk.StringVar(value=str(self.config.get("work_mins", 25)))
        ttk.Entry(session_frame, textvariable=self.work_mins_var, width=10).grid(
            row=0, column=1, padx=10
        )

        # Short break duration
        ttk.Label(session_frame, text="Short Break (minutes):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.short_break_var = tk.StringVar(
            value=str(self.config.get("short_break_mins", 5))
        )
        ttk.Entry(session_frame, textvariable=self.short_break_var, width=10).grid(
            row=1, column=1, padx=10
        )

        # Long break duration
        ttk.Label(session_frame, text="Long Break (minutes):").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.long_break_var = tk.StringVar(
            value=str(self.config.get("long_break_mins", 15))
        )
        ttk.Entry(session_frame, textvariable=self.long_break_var, width=10).grid(
            row=2, column=1, padx=10
        )

        # Music settings tab
        music_frame = ttk.Frame(notebook, padding="10")
        notebook.add(music_frame, text="Music")

        # Enable classical music
        self.music_enabled_var = tk.BooleanVar(
            value=self.config.get("classical_music", True)
        )
        ttk.Checkbutton(
            music_frame, text="Enable Classical Music", variable=self.music_enabled_var
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Music volume
        ttk.Label(music_frame, text="Music Volume (0-100):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.volume_var = tk.StringVar(
            value=str(self.config.get("classical_music_volume", 30))
        )
        ttk.Entry(music_frame, textvariable=self.volume_var, width=10).grid(
            row=1, column=1, padx=10
        )

        # Pause music on break
        self.pause_on_break_var = tk.BooleanVar(
            value=self.config.get("pause_music_on_break", True)
        )
        ttk.Checkbutton(
            music_frame,
            text="Pause Music During Breaks",
            variable=self.pause_on_break_var,
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Playlist selection
        ttk.Label(music_frame, text="Select Playlist:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )

        # Get available playlists
        from music_controller import MusicController

        music_controller = MusicController(self.config)
        self.available_playlists = music_controller.get_available_playlists()

        # Create playlist options list
        self.playlist_options = ["Auto (First Available)"]
        self.playlist_paths = [None]  # None means auto-select

        for playlist in self.available_playlists:
            self.playlist_options.append(playlist["name"])
            self.playlist_paths.append(playlist["path"])

        # Get currently selected playlist
        current_selected = self.config.get("classical_music_selected_playlist")
        current_index = 0  # Default to "Auto"

        if current_selected:
            for i, path in enumerate(self.playlist_paths[1:], 1):  # Skip index 0 (Auto)
                if path == current_selected:
                    current_index = i
                    break

        self.playlist_var = tk.StringVar(value=self.playlist_options[current_index])
        playlist_combo = ttk.Combobox(
            music_frame,
            textvariable=self.playlist_var,
            values=self.playlist_options,
            state="readonly",
            width=25,
        )
        playlist_combo.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

        # Notification settings tab
        notify_frame = ttk.Frame(notebook, padding="10")
        notebook.add(notify_frame, text="Notifications")

        # Enable notifications
        self.notify_enabled_var = tk.BooleanVar(
            value=self.config.get("desktop_notifications", True)
        )
        ttk.Checkbutton(
            notify_frame,
            text="Enable Desktop Notifications",
            variable=self.notify_enabled_var,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Early warning
        ttk.Label(notify_frame, text="Early Warning (minutes):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.warning_var = tk.StringVar(
            value=str(self.config.get("notify_early_warning", 2))
        )
        ttk.Entry(notify_frame, textvariable=self.warning_var, width=10).grid(
            row=1, column=1, padx=10
        )

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=self.cancel_settings).pack(
            side=tk.LEFT, padx=5
        )

    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Session settings
            self.config.set("work_mins", int(self.work_mins_var.get()))
            self.config.set("short_break_mins", int(self.short_break_var.get()))
            self.config.set("long_break_mins", int(self.long_break_var.get()))

            # Music settings
            self.config.set("classical_music", self.music_enabled_var.get())
            self.config.set("classical_music_volume", int(self.volume_var.get()))
            self.config.set("pause_music_on_break", self.pause_on_break_var.get())

            # Save selected playlist
            selected_playlist_name = self.playlist_var.get()
            selected_index = self.playlist_options.index(selected_playlist_name)
            selected_playlist_path = self.playlist_paths[selected_index]

            if selected_playlist_path is None:
                # "Auto" selected - remove any specific selection
                self.config.set("classical_music_selected_playlist", "")
            else:
                self.config.set(
                    "classical_music_selected_playlist", selected_playlist_path
                )

            # Notification settings
            self.config.set("desktop_notifications", self.notify_enabled_var.get())
            self.config.set("notify_early_warning", int(self.warning_var.get()))

            # Save to file
            self.config.save_config()

            self.result = True
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please enter valid numbers for all numeric fields."
            )

    def cancel_settings(self):
        """Cancel settings changes"""
        self.dialog.destroy()


if __name__ == "__main__":
    # Run the GUI application
    try:
        app = FocusGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Focus Timer GUI closed by user")
    except Exception as e:
        print(f"❌ Error running GUI: {e}")
        import traceback

        traceback.print_exc()
