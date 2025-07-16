#!/usr/bin/env python3
"""
GUI Focus Timer for Enhanced Focus Timer
Cross-platform GUI using tkinter with modern styling
"""

import tkinter as tk
from tkinter import messagebox, ttk

from config_manager import ConfigManager

# Removed old InlineTaskWidget import - now using native task management
from music_controller import MusicController
from notification_manager import NotificationManager
from session_manager import SessionManager, SessionState, SessionType
from task_manager import TaskManager


class FocusGUI:
    """Modern GUI for the Focus Timer application"""

    def __init__(self):
        """Initialize the GUI application"""
        try:
            # Initialize components
            self.config = ConfigManager()
            self.music = MusicController(self.config)
            self.notifications = NotificationManager(self.config)
            self.session_manager = SessionManager(
                self.config, self.music, self.notifications
            )

            # Initialize task manager
            self.task_manager = TaskManager()

            # Add a variable to store the current task ID
            self.current_task_id = None

            # Store scheduled callback IDs for proper cleanup
            self.scheduled_callbacks = []

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
            self.setup_keyboard_shortcuts()

            # Show task input dialog if no tasks exist for today
            self.schedule_callback(100, self.check_and_show_task_dialog)

            # Start update loop
            self.schedule_callback(100, self.update_loop)

        except Exception as e:
            print(f"[X] Error initializing GUI: {e}")
            import traceback

            traceback.print_exc()
            raise

    def setup_window(self):
        """Configure the main window"""
        self.root.title("🎯 Enhanced Focus Timer")
        self.root.resizable(True, True)  # Enable resizing

        # Set minimum window size to prevent it from becoming too small
        # Further reduced minimum width for very compact windows
        self.root.minsize(250, 450)

        # Configure grid weights for proper expansion
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Load saved window dimensions or use defaults
        self.load_window_dimensions()

        # Bind resize event to adjust fonts
        self.root.bind("<Configure>", self.on_window_resize)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_window_dimensions(self):
        """Load saved window dimensions or use defaults"""
        try:
            # Try to load saved dimensions from config
            saved_geometry = self.config.get("window_geometry", None)

            if saved_geometry:
                # Parse saved geometry (format: "widthxheight+x+y")
                self.root.geometry(saved_geometry)
            else:
                # Use default centered position
                self.center_window_default()

        except Exception as e:
            # Fall back to default if loading fails
            self.center_window_default()

    def center_window_default(self):
        """Center window with default dimensions"""
        # Default size optimized for compact usage
        default_width = 420
        default_height = 600

        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2

        self.root.geometry(f"{default_width}x{default_height}+{x}+{y}")

    def save_window_dimensions(self):
        """Save current window dimensions"""
        try:
            # Get current window geometry
            geometry = self.root.geometry()
            # Save to config
            self.config.set("window_geometry", geometry)
            self.config.save_config()
        except Exception as e:
            # Silently ignore save errors
            pass

    def calculate_font_sizes(self, window_width):
        """Calculate font sizes based on window width"""
        # Base sizes for 420px width (new more compact default)
        base_width = 420
        ratio = window_width / base_width

        # Scale fonts with more aggressive scaling for very small windows
        # Title font: scale from 18 down to 10 for very small windows
        title_size = max(10, min(22, int(18 * ratio)))

        # Time font: scale from 36 down to 18 for very small windows
        time_size = max(18, min(42, int(36 * ratio)))

        # Normal text: scale from 9 down to 7
        normal_size = max(7, min(11, int(9 * ratio)))

        # Small text: scale from 7 down to 6
        small_size = max(6, min(9, int(7 * ratio)))

        # Button text: scale from 8 down to 6
        button_size = max(6, min(10, int(8 * ratio)))

        return {
            "title": title_size,
            "time": time_size,
            "normal": normal_size,
            "small": small_size,
            "button": button_size,
        }

    def calculate_ui_scaling(self, window_width):
        """Calculate scaling factors for all UI elements based on window width"""
        # Base dimensions for 420px width (compact default)
        base_width = 420
        ratio = window_width / base_width

        # More aggressive scaling for very small windows
        ratio = max(0.6, min(1.5, ratio))  # Limit scaling between 60% and 150%

        return {
            # Padding and spacing
            "main_padding": max(4, int(8 * ratio)),
            "task_padding": max(2, int(4 * ratio)),
            "button_padx": max(1, int(3 * ratio)),
            "button_pady": max(1, int(3 * ratio)),
            "frame_pady": max(2, int(8 * ratio)),
            "small_pady": max(1, int(2 * ratio)),
            # Widget sizes
            "button_width": max(8, int(15 * ratio)),
            "small_button_width": max(2, int(3 * ratio)),
            "spinbox_width": max(2, int(3 * ratio)),
            "entry_height": max(1, int(1 * ratio)),
            "progress_height": max(15, int(25 * ratio)),
            # Canvas and container heights
            "canvas_height": max(60, int(120 * ratio)),
            "task_row_height": max(20, int(30 * ratio)),
            # Border and spacing
            "border_width": max(1, int(1 * ratio)),
            "separator_height": max(1, int(2 * ratio)),
        }

    def on_window_resize(self, event):
        """Handle window resize events to adjust font sizes and UI scaling"""
        # Only respond to main window resize events
        if event.widget == self.root:
            window_width = self.root.winfo_width()
            if window_width > 0:  # Ensure valid width
                self.update_font_sizes(window_width)
                self.update_ui_scaling(window_width)

    def update_font_sizes(self, window_width):
        """Update all font sizes based on window width"""
        sizes = self.calculate_font_sizes(window_width)

        try:
            # Update title font
            self.title_label.configure(font=("Arial", sizes["title"], "bold"))

            # Update time display font
            self.time_label.configure(font=("Courier New", sizes["time"], "bold"))

            # Update status label fonts
            if hasattr(self, "music_status_label"):
                self.music_status_label.configure(font=("Arial", sizes["small"]))
            if hasattr(self, "session_count_label"):
                self.session_count_label.configure(font=("Arial", sizes["small"]))

            # Update task-related fonts if they exist
            if hasattr(self, "task_stats_label"):
                self.task_stats_label.configure(font=("Arial", sizes["small"]))
            if hasattr(self, "task_entry"):
                self.task_entry.configure(font=("Arial", sizes["normal"]))

            # Update button font
            style = ttk.Style()
            style.configure(
                "Modern.TButton", font=("Segoe UI", sizes["button"], "bold")
            )

            # Update main frame padding for very small windows (legacy - will be handled by update_ui_scaling)
            if window_width < 300:
                self.main_frame.configure(padding="4")
            elif window_width < 350:
                self.main_frame.configure(padding="6")
            else:
                self.main_frame.configure(padding="8")

        except Exception as e:
            # Silently handle any font update errors to prevent crashes
            pass

    def update_ui_scaling(self, window_width):
        """Update all UI element sizes and spacing based on window width"""
        scaling = self.calculate_ui_scaling(window_width)

        try:
            # Update main frame padding
            self.main_frame.configure(padding=str(scaling["main_padding"]))

            # Update task frame padding if it exists
            if hasattr(self, "task_frame"):
                self.task_frame.configure(padding=str(scaling["task_padding"]))

            # Update button spacing in session frame
            if hasattr(self, "session_frame"):
                for child in self.session_frame.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.grid_configure(
                            padx=scaling["button_padx"], pady=scaling["button_pady"]
                        )

            # Update control frame button spacing
            if hasattr(self, "control_frame"):
                for child in self.control_frame.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.grid_configure(padx=scaling["button_padx"])

            # Update additional frame button spacing
            if hasattr(self, "additional_frame"):
                for child in self.additional_frame.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.grid_configure(
                            padx=scaling["button_padx"], pady=scaling["button_pady"]
                        )

            # Update progress bar height and padding
            if hasattr(self, "progress_bar"):
                # For progressbar height, we need to use style configuration
                style = ttk.Style()
                style.configure(
                    "Scaled.Horizontal.TProgressbar",
                    thickness=scaling["progress_height"],
                )
                self.progress_bar.configure(style="Scaled.Horizontal.TProgressbar")

                # Update progress bar grid padding
                self.progress_bar.grid_configure(pady=(0, scaling["frame_pady"]))

            # Update spinbox width in task entry
            if hasattr(self, "pomodoro_spinbox"):
                self.pomodoro_spinbox.configure(width=scaling["spinbox_width"])

            # Update small button widths in task entry
            if hasattr(self, "add_task_frame"):
                for child in self.add_task_frame.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.configure(width=scaling["small_button_width"])

            # Update canvas height if it exists
            if hasattr(self, "tasks_canvas"):
                # Calculate dynamic height based on window size and available space
                window_height = self.root.winfo_height()
                # Reserve space for other elements (approximately 400px at default size)
                reserved_space = int(400 * (window_width / 420))
                available_height = max(
                    scaling["canvas_height"], window_height - reserved_space
                )
                self.tasks_canvas.configure(height=available_height)

            # Update title and time label padding
            if hasattr(self, "title_label"):
                self.title_label.grid_configure(pady=(0, scaling["frame_pady"]))
            if hasattr(self, "time_label"):
                self.time_label.grid_configure(pady=(0, scaling["frame_pady"]))

            # Update progress bar padding
            if hasattr(self, "progress_bar"):
                self.progress_bar.grid_configure(
                    pady=(0, scaling["frame_pady"]), padx=scaling["main_padding"]
                )

            # Update status frame spacing and labels
            if hasattr(self, "status_frame"):
                self.status_frame.grid_configure(pady=(0, scaling["frame_pady"]))
                # Update status label spacing
                if hasattr(self, "music_status_label"):
                    self.music_status_label.grid_configure(padx=scaling["main_padding"])
                if hasattr(self, "session_count_label"):
                    self.session_count_label.grid_configure(
                        padx=scaling["main_padding"]
                    )

            # Update task entry spacing if it exists
            if hasattr(self, "task_entry"):
                self.task_entry.grid_configure(padx=(0, scaling["button_padx"]))

            # Update task frame spacing
            if hasattr(self, "task_frame"):
                self.task_frame.grid_configure(
                    pady=(scaling["small_pady"], scaling["small_pady"])
                )

            # Update tasks container spacing
            if hasattr(self, "tasks_container"):
                self.tasks_container.grid_configure(pady=(scaling["frame_pady"], 0))

            # Update frame spacing for session, control, and additional frames
            if hasattr(self, "session_frame"):
                self.session_frame.grid_configure(pady=(0, scaling["frame_pady"]))
            if hasattr(self, "control_frame"):
                self.control_frame.grid_configure(pady=(0, scaling["frame_pady"]))

            # Refresh task display to apply scaling to task rows
            if hasattr(self, "update_task_display"):
                self.update_task_display()

        except Exception as e:
            # Silently handle any UI scaling errors to prevent crashes
            pass

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Calculate initial font sizes and UI scaling based on new compact default
        initial_sizes = self.calculate_font_sizes(420)  # New compact default width
        initial_scaling = self.calculate_ui_scaling(420)  # Calculate initial UI scaling

        # Main frame with dynamic padding
        self.main_frame = ttk.Frame(
            self.root, padding=str(initial_scaling["main_padding"])
        )
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure main frame grid weights for proper scaling
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        # Configure row weights - give more weight to the task section
        self.main_frame.grid_rowconfigure(0, weight=0)  # Title (fixed)
        self.main_frame.grid_rowconfigure(1, weight=0)  # Time display (fixed)
        self.main_frame.grid_rowconfigure(2, weight=0)  # Progress bar (fixed)
        self.main_frame.grid_rowconfigure(3, weight=0)  # Session buttons (fixed)
        self.main_frame.grid_rowconfigure(4, weight=0)  # Control buttons (fixed)
        self.main_frame.grid_rowconfigure(5, weight=0)  # Status (fixed)
        self.main_frame.grid_rowconfigure(6, weight=1)  # Task section (expandable)
        self.main_frame.grid_rowconfigure(7, weight=0)  # Additional buttons (fixed)

        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="🎯 FOCUS TIMER",
            font=("Arial", initial_sizes["title"], "bold"),
        )
        self.title_label.grid(
            row=0, column=0, columnspan=3, pady=(0, initial_scaling["frame_pady"])
        )

        # Time display
        self.time_label = ttk.Label(
            self.main_frame,
            text="00:00",
            font=("Courier New", initial_sizes["time"], "bold"),
        )
        self.time_label.grid(
            row=1, column=0, columnspan=3, pady=(0, initial_scaling["frame_pady"])
        )

        # Progress bar with dynamic height
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.configure(
            "Scaled.Horizontal.TProgressbar",
            thickness=initial_scaling["progress_height"],
        )
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            variable=self.progress_var,
            maximum=100,
            style="Scaled.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(
            row=2,
            column=0,
            columnspan=3,
            pady=(0, initial_scaling["frame_pady"]),
            sticky=(tk.W, tk.E),
            padx=initial_scaling["main_padding"],
        )

        # Session buttons frame
        self.session_frame = ttk.Frame(self.main_frame)
        self.session_frame.grid(
            row=3, column=0, columnspan=3, pady=(0, initial_scaling["frame_pady"])
        )

        # Configure session frame for scaling
        self.session_frame.grid_columnconfigure(0, weight=1)
        self.session_frame.grid_columnconfigure(1, weight=1)

        # Session buttons with dynamic scaling
        self.work_button = ttk.Button(
            self.session_frame,
            text=f"Work Session ({self.config.get('work_mins')} min)",
            command=lambda: self.start_session(SessionType.WORK),
            style="Modern.TButton",
        )
        self.work_button.grid(
            row=0,
            column=0,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        self.short_break_button = ttk.Button(
            self.session_frame,
            text=f"Short Break ({self.config.get('short_break_mins')} min)",
            command=lambda: self.start_session(SessionType.SHORT_BREAK),
            style="Modern.TButton",
        )
        self.short_break_button.grid(
            row=0,
            column=1,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        self.long_break_button = ttk.Button(
            self.session_frame,
            text=f"Long Break ({self.config.get('long_break_mins')} min)",
            command=lambda: self.start_session(SessionType.LONG_BREAK),
            style="Modern.TButton",
        )
        self.long_break_button.grid(
            row=1,
            column=0,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        self.custom_button = ttk.Button(
            self.session_frame,
            text="Custom Session",
            command=self.start_custom_session,
            style="Modern.TButton",
        )
        self.custom_button.grid(
            row=1,
            column=1,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        # Control buttons frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(
            row=4, column=0, columnspan=3, pady=(0, initial_scaling["frame_pady"])
        )

        # Configure control frame for scaling
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_columnconfigure(1, weight=1)
        self.control_frame.grid_columnconfigure(2, weight=1)

        # Control buttons with dynamic spacing
        self.pause_button = ttk.Button(
            self.control_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            state="disabled",
            style="Modern.TButton",
        )
        self.pause_button.grid(
            row=0, column=0, padx=initial_scaling["button_padx"], sticky=(tk.W, tk.E)
        )

        self.stop_button = ttk.Button(
            self.control_frame,
            text="⏹ Stop",
            command=self.stop_session,
            state="disabled",
            style="Modern.TButton",
        )
        self.stop_button.grid(
            row=0, column=1, padx=initial_scaling["button_padx"], sticky=(tk.W, tk.E)
        )

        self.music_button = ttk.Button(
            self.control_frame,
            text="🎵 Music",
            command=self.toggle_music,
            style="Modern.TButton",
        )
        self.music_button.grid(
            row=0, column=2, padx=initial_scaling["button_padx"], sticky=(tk.W, tk.E)
        )

        # Status frame
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.grid(
            row=5, column=0, columnspan=3, pady=(0, initial_scaling["frame_pady"])
        )
        self.additional_frame = ttk.Frame(self.main_frame)
        self.additional_frame.grid(row=7, column=0, columnspan=3)

        # Configure additional frame for scaling
        self.additional_frame.grid_columnconfigure(0, weight=1)
        self.additional_frame.grid_columnconfigure(1, weight=1)
        self.additional_frame.grid_columnconfigure(2, weight=1)

        # Additional buttons with dynamic spacing
        self.stats_button = ttk.Button(
            self.additional_frame,
            text="📊 Statistics",
            command=self.show_statistics,
            style="Modern.TButton",
        )
        self.stats_button.grid(
            row=0,
            column=0,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        self.settings_button = ttk.Button(
            self.additional_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            style="Modern.TButton",
        )
        self.settings_button.grid(
            row=0,
            column=1,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        self.test_button = ttk.Button(
            self.additional_frame,
            text="🧪 Test Music",
            command=self.test_music,
            style="Modern.TButton",
        )
        self.test_button.grid(
            row=0,
            column=2,
            padx=initial_scaling["button_padx"],
            pady=initial_scaling["button_pady"],
            sticky=(tk.W, tk.E),
        )

        # Task Management Section (Native Integration)
        self.create_task_section()

        # Initial display update after all widgets are created
        self.root.after(0, self.update_display)

    def create_task_section(self):
        """Create native task management section in the main GUI"""
        # Get current scaling for dynamic sizing
        current_width = self.root.winfo_width() or 420  # Use 420 as fallback
        scaling = self.calculate_ui_scaling(current_width)

        # Task management frame (minimal, no label frame) with dynamic padding
        self.task_frame = ttk.Frame(
            self.main_frame, padding=str(scaling["task_padding"])
        )
        self.task_frame.grid(
            row=6,
            column=0,
            columnspan=3,
            pady=(scaling["small_pady"], scaling["small_pady"]),
            sticky=(tk.W, tk.E, tk.N, tk.S),
        )
        self.task_frame.grid_columnconfigure(0, weight=1)
        # Set expandable height to grow with window
        self.task_frame.grid_rowconfigure(2, weight=1)  # Tasks display area expands

        # Task state tracking
        self.adding_task = False
        self.typing_active = False

        # Minimal header with just add button and compact stats
        header_frame = ttk.Frame(self.task_frame)
        header_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E), pady=(0, scaling["small_pady"])
        )
        header_frame.grid_columnconfigure(0, weight=1)

        # Compact task stats (minimal)
        self.task_stats_label = tk.Label(
            header_frame,
            text="0/0",
            font=("Arial", 8),
            fg="#00ff00",
            bg="#2b2b2b",
        )
        self.task_stats_label.grid(row=0, column=0, sticky=tk.W)

        # Add task entry frame (overlay style, doesn't expand layout)
        self.add_task_frame = ttk.Frame(self.task_frame)
        # Position as overlay in the tasks area instead of separate row
        self.add_task_frame.grid(
            row=1,
            column=0,
            sticky=(tk.W, tk.E),
            pady=(scaling["small_pady"], scaling["task_padding"]),
        )
        self.add_task_frame.grid_columnconfigure(0, weight=1)

        # Task entry widgets (wider entry field with better color control)
        self.task_entry_var = tk.StringVar()
        self.task_entry = tk.Entry(
            self.add_task_frame,
            textvariable=self.task_entry_var,
            font=("Arial", 10),
            bg="#ffffff",  # White background
            fg="#000000",  # Black text by default
            insertbackground="#000000",  # Black cursor
        )
        self.task_entry.grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, scaling["button_padx"])
        )

        # Placeholder functionality
        self.placeholder_text = "+add"
        self.placeholder_color = "#00cc00"  # Bright green for placeholder
        self.normal_color = "#000000"  # Black text for normal typing
        self.typing_color = "#006600"  # Dark green for active typing
        self.showing_placeholder = False

        # Bind focus events for typing state
        self.task_entry.bind("<FocusIn>", self.on_task_entry_focus_in)
        self.task_entry.bind("<FocusOut>", self.on_task_entry_focus_out)
        self.task_entry.bind("<KeyPress>", self.on_task_entry_key_press)
        self.task_entry.bind("<Return>", lambda e: self.save_new_task())
        self.task_entry.bind("<Escape>", lambda e: self.cancel_add_task())

        # Compact pomodoro count with dynamic spacing
        self.pomodoro_var = tk.IntVar(value=1)
        pomodoro_label = ttk.Label(self.add_task_frame, text="🍅")
        pomodoro_label.grid(
            row=0, column=1, padx=(scaling["button_padx"], scaling["small_pady"])
        )

        self.pomodoro_spinbox = ttk.Spinbox(
            self.add_task_frame,
            from_=1,
            to=10,
            width=scaling["spinbox_width"],
            textvariable=self.pomodoro_var,
        )
        self.pomodoro_spinbox.grid(row=0, column=2, padx=(0, scaling["button_padx"]))

        # Compact save/cancel buttons with dynamic width and spacing
        save_button = ttk.Button(
            self.add_task_frame,
            text="✓",
            command=self.save_new_task,
            width=scaling["small_button_width"],
        )
        save_button.grid(row=0, column=3, padx=(0, scaling["small_pady"]))

        cancel_button = ttk.Button(
            self.add_task_frame,
            text="✗",
            command=self.cancel_add_task,
            width=scaling["small_button_width"],
        )
        cancel_button.grid(row=0, column=4)

        # Always show add task widgets and initialize with placeholder
        self.show_placeholder()

        # Tasks display area with scrolling capability - dynamic spacing
        # Create a frame that can scroll if needed
        self.tasks_container = ttk.Frame(self.task_frame)
        self.tasks_container.grid(
            row=2,
            column=0,
            sticky=(tk.W, tk.E, tk.N, tk.S),
            pady=(scaling["frame_pady"], 0),
        )
        self.tasks_container.grid_columnconfigure(0, weight=1)
        self.tasks_container.grid_rowconfigure(0, weight=1)

        # Canvas for scrolling with dynamic height
        self.tasks_canvas = tk.Canvas(
            self.tasks_container,
            bg="#2b2b2b",
            highlightthickness=0,
            height=scaling["canvas_height"],  # Dynamic canvas height
        )
        self.tasks_scrollbar = ttk.Scrollbar(
            self.tasks_container, orient="vertical", command=self.tasks_canvas.yview
        )
        self.tasks_canvas.configure(yscrollcommand=self.tasks_scrollbar.set)

        # Tasks display frame inside canvas
        self.tasks_display_frame = ttk.Frame(self.tasks_canvas)
        self.tasks_display_frame.grid_columnconfigure(0, weight=1)

        # Create window in canvas
        self.canvas_window = self.tasks_canvas.create_window(
            (0, 0), window=self.tasks_display_frame, anchor="nw"
        )

        # Configure scrolling
        self.tasks_display_frame.bind(
            "<Configure>",
            lambda e: self.tasks_canvas.configure(
                scrollregion=self.tasks_canvas.bbox("all")
            ),
        )
        self.tasks_canvas.bind(
            "<Configure>",
            lambda e: self.tasks_canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # Pack canvas and scrollbar
        self.tasks_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.tasks_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Bind mousewheel to canvas
        self.tasks_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Update task display
        self.update_task_display()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in tasks area"""
        self.tasks_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def hide_add_task_widgets(self):
        """Hide the add task entry widgets"""
        for widget in self.add_task_frame.winfo_children():
            widget.grid_remove()

    def show_add_task_widgets(self):
        """Show the add task entry widgets"""
        for widget in self.add_task_frame.winfo_children():
            widget.grid()

    def show_add_task_entry(self):
        """Show the add task entry interface"""
        if not self.adding_task:
            self.adding_task = True
            self.typing_active = True

            # Clear any existing text and show placeholder
            self.clear_placeholder()  # Ensure clean state first
            self.show_placeholder()
            self.pomodoro_var.set(1)
            self.task_entry.focus_set()

            # Update display
            self.update_task_display()

    def save_new_task(self):
        """Save the new task"""
        task_text = self.task_entry_var.get().strip()
        # Don't save if it's just the placeholder text or empty
        if (
            task_text
            and task_text != self.placeholder_text
            and not self.showing_placeholder
        ):
            pomodoros = self.pomodoro_var.get()
            self.task_manager.add_task(task_text, pomodoros_planned=pomodoros)

        # Always cancel/clear the add task interface
        self.cancel_add_task()

    def cancel_add_task(self):
        """Cancel adding new task"""
        self.adding_task = False
        self.typing_active = False

        # Clear placeholder and reset
        self.clear_placeholder()
        self.show_placeholder()  # Show placeholder again
        self.pomodoro_var.set(1)

        # Return focus to main window
        self.root.focus_set()

        # Update display to restore proper interface
        self.update_task_display()

    def update_task_display(self):
        """Update the task display section"""
        # Clear existing task widgets
        for widget in self.tasks_display_frame.winfo_children():
            widget.destroy()

        # Get tasks and stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        # Show/hide header elements based on state
        if stats["total"] > 0:
            # Show header with stats when there are tasks
            self.task_stats_label.grid(row=0, column=0, sticky=tk.W)
            # Minimal format: "2/5 🍅4/8"
            stats_text = f"{stats['completed']}/{stats['total']} 🍅{stats['total_pomodoros_completed']}/{stats['total_pomodoros_planned']}"
            self.task_stats_label.config(text=stats_text)
        else:
            # No tasks yet - decide what to show based on typing state
            if self.adding_task:
                # Show minimal header when typing (no stats)
                self.task_stats_label.grid_remove()
            else:
                # Hide entire header when showing empty state interface
                self.task_stats_label.grid_remove()

        # Display content based on state
        if not tasks and not self.adding_task:
            # Show attractive "Add your first task" interface
            self.create_empty_state_interface()
        elif not tasks and self.adding_task:
            # When typing but no tasks yet - show nothing in task area (input is at top)
            pass
        else:
            # Display existing tasks
            for i, task in enumerate(tasks):
                self.create_task_row(self.tasks_display_frame, task, i)

        # Update scroll region
        self.root.after_idle(
            lambda: self.tasks_canvas.configure(
                scrollregion=self.tasks_canvas.bbox("all")
            )
        )

    def create_task_row(self, parent, task, row):
        """Create a compact task row in the display"""
        # Get current scaling for dynamic sizing
        current_width = self.root.winfo_width() or 420
        scaling = self.calculate_ui_scaling(current_width)

        # Task row frame (more compact) with dynamic spacing
        task_row = ttk.Frame(parent)
        if task.id == self.current_task_id:
            task_row.configure(style="Current.TFrame")

        task_row.grid(
            row=row,
            column=0,
            sticky=(tk.W, tk.E),
            pady=scaling["small_pady"],
            padx=scaling["small_pady"],
        )
        task_row.grid_columnconfigure(1, weight=1)  # Title column expands

        # Completion checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_row,
            variable=completed_var,
            command=lambda: self.toggle_task(task, completed_var),
        )
        check.grid(row=0, column=0, padx=(0, scaling["button_padx"]))

        # Task title (more compact)
        title_text = task.title
        if task.completed:
            title_text = f"✅ {title_text}"
            text_color = "#666666"
        else:
            text_color = "#00ff00"

        title_label = tk.Label(
            task_row,
            text=title_text,
            font=("Arial", 9),  # Smaller font
            fg=text_color,
            bg="#2b2b2b",
            anchor="w",
        )
        title_label.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, scaling["small_pady"])
        )
        title_label.bind(
            "<Double-1>", lambda event, task=task: self.edit_task_title(event, task)
        )

        # Compact pomodoro progress
        pomodoro_text = f"{task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_color = "#00cc00" if task.pomodoros_completed > 0 else "#666666"

        pomodoro_label = tk.Label(
            task_row,
            text=pomodoro_text,
            font=("Arial", 8),  # Smaller font
            fg=pomodoro_color,
            bg="#2b2b2b",
        )
        pomodoro_label.grid(
            row=0, column=2, padx=(scaling["small_pady"], scaling["small_pady"])
        )

        # Compact pomodoro buttons (for incomplete tasks) with dynamic width
        if not task.completed:
            # Decrease pomodoro button (only if task has completed pomodoros)
            if task.pomodoros_completed > 0:
                decrease_pomodoro_btn = ttk.Button(
                    task_row,
                    text="-",
                    command=lambda: self.remove_pomodoro_from_task(task),
                    width=scaling["small_button_width"],
                )
                decrease_pomodoro_btn.grid(
                    row=0,
                    column=3,
                    padx=(scaling["small_pady"], scaling["small_pady"] // 2),
                )

                # Add pomodoro button
                add_pomodoro_btn = ttk.Button(
                    task_row,
                    text="+",
                    command=lambda: self.add_pomodoro_to_task(task),
                    width=scaling["small_button_width"],
                )
                add_pomodoro_btn.grid(
                    row=0,
                    column=4,
                    padx=(scaling["small_pady"] // 2, scaling["small_pady"]),
                )
                delete_column = 5
            else:
                # Only add button when no completed pomodoros
                add_pomodoro_btn = ttk.Button(
                    task_row,
                    text="+",
                    command=lambda: self.add_pomodoro_to_task(task),
                    width=scaling["small_button_width"],
                )
                add_pomodoro_btn.grid(
                    row=0, column=3, padx=(scaling["small_pady"], scaling["small_pady"])
                )
                delete_column = 4
        else:
            delete_column = 3

        # Compact delete button with dynamic width
        delete_btn = ttk.Button(
            task_row,
            text="×",
            command=lambda: self.delete_task(task.id),
            width=scaling["small_button_width"],
        )
        delete_btn.grid(row=0, column=delete_column, padx=(scaling["small_pady"], 0))

    def edit_task_title(self, event, task):
        """Handle double-click to edit a task title."""
        # Create an entry widget over the label
        entry = ttk.Entry(event.widget.master, font=("Arial", 9))
        entry.insert(0, task.title)
        entry.place(
            x=event.widget.winfo_x(),
            y=event.widget.winfo_y(),
            width=event.widget.winfo_width(),
            height=event.widget.winfo_height(),
        )
        entry.focus_set()

        def save_edit(event):
            new_title = entry.get().strip()
            if new_title:
                self.task_manager.update_task_title(task.id, new_title)
            entry.destroy()
            self.update_task_display()

        def cancel_edit(event):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", cancel_edit)

    def toggle_task(self, task, var):
        """Toggle task completion"""
        if var.get():
            self.task_manager.complete_task(task.id)
        else:
            # Uncomplete task
            task.completed = False
            task.completed_at = None
            self.task_manager.save_tasks()
        self.update_task_display()

    def add_pomodoro_to_task(self, task):
        """Add a pomodoro to a task"""
        self.task_manager.add_pomodoro_to_task(task.id)
        self.update_task_display()

    def remove_pomodoro_from_task(self, task):
        """Remove a pomodoro from a task"""
        self.task_manager.remove_pomodoro_from_task(task.id)
        self.update_task_display()

    def delete_task(self, task_id):
        """Delete a specific task"""
        self.task_manager.delete_task(task_id)
        self.update_task_display()

    def delete_last_task(self):
        """Delete the most recently added task"""
        tasks = self.task_manager.get_today_tasks()
        if tasks:
            # Delete the first task (most recently added since we insert at top)
            self.task_manager.delete_task(tasks[0].id)
            self.update_task_display()

    def trigger_add_task(self):
        """Public method to trigger adding a new task (for keyboard shortcuts)"""
        # Since the entry is always visible, just focus it
        self.task_entry.focus_set()
        if self.showing_placeholder:
            self.clear_placeholder()
            self.adding_task = True
            self.typing_active = True

    def is_typing(self):
        """Check if user is currently typing in task entry"""
        return getattr(self, "typing_active", False)

    def on_task_entry_focus_in(self, event):
        """Handle task entry focus in"""
        self.typing_active = True
        # Clear placeholder when focused
        if self.showing_placeholder:
            self.task_entry_var.set("")
            self.showing_placeholder = False
            event.widget.configure(foreground=self.typing_color)
        else:
            # Change entry color to dark green while typing
            event.widget.configure(foreground=self.typing_color)

    def on_task_entry_focus_out(self, event):
        """Handle task entry focus out"""
        self.typing_active = False
        # Show placeholder if entry is empty
        if not self.task_entry_var.get().strip():
            self.show_placeholder()
        else:
            # Restore normal color
            event.widget.configure(foreground=self.normal_color)

    def on_task_entry_key_press(self, event):
        """Handle key press in task entry"""
        self.typing_active = True

        # Clear placeholder on first keypress
        if self.showing_placeholder:
            # Clear placeholder and allow the keystroke to be processed
            self.root.after(
                1,
                lambda: (
                    self.task_entry_var.set(""),
                    setattr(self, "showing_placeholder", False),
                    self.task_entry.configure(foreground=self.typing_color),
                ),
            )

    def show_placeholder(self):
        """Show placeholder text in task entry"""
        if not self.task_entry_var.get().strip():
            self.task_entry_var.set(self.placeholder_text)
            self.task_entry.configure(foreground=self.placeholder_color)
            self.showing_placeholder = True

    def clear_placeholder(self):
        """Clear placeholder text from task entry"""
        # Always clear the entry field and reset state
        self.task_entry_var.set("")
        self.task_entry.configure(foreground=self.normal_color)
        self.showing_placeholder = False

    def create_empty_state_interface(self):
        """Create an attractive interface when no tasks exist"""
        # Main empty state container
        empty_container = ttk.Frame(self.tasks_display_frame)
        empty_container.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=30)
        empty_container.grid_columnconfigure(0, weight=1)

        # Attractive message with icon
        message_label = tk.Label(
            empty_container,
            text="🎯 Add first task!",
            font=("Arial", 12, "bold"),
            fg="#00ff00",
            bg="#2b2b2b",
            justify="center",
        )
        message_label.grid(row=0, column=0, pady=(0, 15))

        # Instruction text
        instruction_label = tk.Label(
            empty_container,
            text="'T' key to add task",
            font=("Arial", 10, "italic"),
            fg="#888888",
            bg="#2b2b2b",
            justify="center",
        )
        instruction_label.grid(row=1, column=0, pady=(0, 20))

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

                style.configure(
                    "TLabel",
                    background=bg_color,
                    foreground=fg_color,
                    font=("Segoe UI", 9),
                )
                style.configure("TFrame", background=bg_color)
                style.configure(
                    "TProgressbar", background=accent_color, troughcolor=select_color
                )
                style.configure("Current.TFrame", background=select_color)

                # Modern button style
                style.configure(
                    "Modern.TButton",
                    background=select_color,
                    foreground=fg_color,
                    borderwidth=0,
                    focusthickness=0,
                    padding=10,
                    font=("Segoe UI", 10, "bold"),
                )
                style.map(
                    "Modern.TButton",
                    background=[("active", accent_color), ("pressed", accent_color)],
                    foreground=[("active", bg_color)],
                )

                self.root.configure(bg=bg_color)

            except tk.TclError as e:
                print(f"Error applying theme: {e}")
                pass  # Fall back to default theme

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for quick actions"""
        # T key - Add new task
        self.root.bind("<KeyPress-t>", lambda e: self.shortcut_add_task())
        self.root.bind("<KeyPress-T>", lambda e: self.shortcut_add_task())

        # M key - Toggle music
        self.root.bind("<KeyPress-m>", lambda e: self.shortcut_toggle_music())
        self.root.bind("<KeyPress-M>", lambda e: self.shortcut_toggle_music())

        # D key - Delete last/selected task
        self.root.bind("<KeyPress-d>", lambda e: self.shortcut_delete_task())
        self.root.bind("<KeyPress-D>", lambda e: self.shortcut_delete_task())

        # W key - Open tasks in separate window
        self.root.bind("<KeyPress-w>", lambda e: self.shortcut_open_task_window())
        self.root.bind("<KeyPress-W>", lambda e: self.shortcut_open_task_window())

        # Alternative bindings using <Key> events (more reliable)
        self.root.bind("<Key-t>", lambda e: self.shortcut_add_task())
        self.root.bind("<Key-T>", lambda e: self.shortcut_add_task())
        self.root.bind("<Key-d>", lambda e: self.shortcut_delete_task())
        self.root.bind("<Key-D>", lambda e: self.shortcut_delete_task())
        self.root.bind("<Key-m>", lambda e: self.shortcut_toggle_music())
        self.root.bind("<Key-M>", lambda e: self.shortcut_toggle_music())
        self.root.bind("<Key-w>", lambda e: self.shortcut_open_task_window())
        self.root.bind("<Key-W>", lambda e: self.shortcut_open_task_window())

        # Ensure the main window can receive focus for shortcuts
        self.root.focus_set()
        self.root.focus_force()

        # Set up a periodic focus refresh to ensure shortcuts always work
        self.schedule_callback(1000, self.refresh_keyboard_focus)

    def refresh_keyboard_focus(self):
        """Periodically refresh keyboard focus to ensure shortcuts continue working"""
        try:
            # Only set focus if no widget currently has focus or if not typing
            focused_widget = self.root.focus_get()
            if not focused_widget or not self.typing_active:
                self.root.focus_set()
        except:
            pass  # Ignore focus errors

        # Schedule next refresh
        self.schedule_callback(2000, self.refresh_keyboard_focus)

    def shortcut_add_task(self):
        """Handle T key shortcut to focus task entry"""
        if not self.typing_active:
            # Since the entry is always visible, just focus it
            self.task_entry.focus_set()
            # Clear placeholder if present
            if self.showing_placeholder:
                self.clear_placeholder()
                self.adding_task = True
                self.typing_active = True

    def shortcut_toggle_music(self):
        """Handle M key shortcut to toggle music"""
        if not self.typing_active:
            self.toggle_music()
            # Return focus to main window to ensure shortcuts continue working
            self.root.after(50, self.root.focus_set)

    def shortcut_delete_task(self):
        """Handle D key shortcut to delete the last task"""
        if not self.typing_active:
            self.delete_last_task()
            # Return focus to main window to ensure shortcuts continue working
            self.root.after(50, self.root.focus_set)

    def shortcut_open_task_window(self):
        """Handle W key shortcut to open task window"""
        if not self.typing_active:
            self.open_task_window()

    def open_task_window(self):
        """Open tasks in a separate window"""
        if hasattr(self, "task_window") and self.task_window.winfo_exists():
            # If window already exists, bring it to front
            self.task_window.lift()
            self.task_window.focus_force()
            return

        # Create new task window
        self.task_window = tk.Toplevel(self.root)
        self.task_window.title("📝 Task Manager")
        self.task_window.geometry("500x400")
        self.task_window.resizable(True, True)
        self.task_window.minsize(400, 300)  # Set minimum size

        # Apply dark theme to the window
        self.task_window.configure(bg="#2b2b2b")

        # Center window on screen
        self.task_window.update_idletasks()
        x = (self.task_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.task_window.winfo_screenheight() // 2) - (400 // 2)
        self.task_window.geometry(f"500x400+{x}+{y}")

        # Create native task management UI for the separate window
        self.create_separate_task_ui()

        # Bind window close to cleanup
        self.task_window.protocol("WM_DELETE_WINDOW", self.close_task_window)

    def close_task_window(self):
        """Close the separate task window"""
        if hasattr(self, "task_window"):
            self.task_window.destroy()
            delattr(self, "task_window")
        # Refresh the main task display
        self.update_task_display()

    def check_and_show_task_dialog(self):
        """Check if tasks exist for today and prompt user to add some"""
        # Since the task entry is always visible, we don't need to show it
        # The placeholder text will guide users to add their first task
        pass

    def create_separate_task_ui(self):
        """Create task management UI for the separate window"""
        # Main frame
        main_frame = ttk.Frame(self.task_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="📝 Task Manager", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Task management frame (reuse the same logic as main GUI)
        self.separate_task_frame = ttk.LabelFrame(
            main_frame, text="Today's Tasks", padding="8"
        )
        self.separate_task_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.separate_task_frame.grid_columnconfigure(0, weight=1)

        # Add task interface
        self.create_separate_add_task_ui()

        # Tasks display
        self.separate_tasks_display = ttk.Frame(self.separate_task_frame)
        self.separate_tasks_display.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0)
        )
        self.separate_tasks_display.grid_columnconfigure(0, weight=1)

        # Update display
        self.update_separate_task_display()

    def create_separate_add_task_ui(self):
        """Create add task UI for separate window"""
        # Header with add button
        header_frame = ttk.Frame(self.separate_task_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        # Stats label
        self.separate_stats_label = tk.Label(
            header_frame,
            text="No tasks yet",
            font=("Arial", 10),
            fg="#00ff00",
            bg="#2b2b2b",
        )
        self.separate_stats_label.grid(row=0, column=0, sticky=tk.W)

        # Add button
        add_button = ttk.Button(
            header_frame,
            text="➕ Add Task",
            command=self.show_separate_add_entry,
            width=12,
        )
        add_button.grid(row=0, column=1, sticky=tk.E)

        # Add task entry frame
        self.separate_add_frame = ttk.Frame(self.separate_task_frame)
        self.separate_add_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        self.separate_add_frame.grid_columnconfigure(0, weight=1)

        # Entry widgets
        self.separate_task_var = tk.StringVar()
        self.separate_entry = ttk.Entry(
            self.separate_add_frame,
            textvariable=self.separate_task_var,
            font=("Arial", 10),
        )
        self.separate_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.separate_pomodoro_var = tk.IntVar(value=1)
        ttk.Label(self.separate_add_frame, text="🍅").grid(row=0, column=1, padx=(0, 2))

        self.separate_spinbox = ttk.Spinbox(
            self.separate_add_frame,
            from_=1,
            to=10,
            width=3,
            textvariable=self.separate_pomodoro_var,
        )
        self.separate_spinbox.grid(row=0, column=2, padx=(0, 5))

        # Buttons
        ttk.Button(
            self.separate_add_frame,
            text="✓",
            command=self.save_separate_task,
            width=3,
        ).grid(row=0, column=3, padx=(0, 2))

        ttk.Button(
            self.separate_add_frame,
            text="✗",
            command=self.cancel_separate_add,
            width=3,
        ).grid(row=0, column=4)

        # Bind enter key
        self.separate_entry.bind("<Return>", lambda e: self.save_separate_task())
        self.separate_entry.bind("<Escape>", lambda e: self.cancel_separate_add())

        # Hide initially
        self.hide_separate_add_widgets()

    def show_separate_add_entry(self):
        """Show add task entry in separate window"""
        for widget in self.separate_add_frame.winfo_children():
            widget.grid()
        self.separate_task_var.set("")
        self.separate_pomodoro_var.set(1)
        self.separate_entry.focus_set()

    def hide_separate_add_widgets(self):
        """Hide add task widgets in separate window"""
        for widget in self.separate_add_frame.winfo_children():
            widget.grid_remove()

    def save_separate_task(self):
        """Save task from separate window"""
        task_text = self.separate_task_var.get().strip()
        if task_text:
            pomodoros = self.separate_pomodoro_var.get()
            self.task_manager.add_task(task_text, pomodoros_planned=pomodoros)
        self.cancel_separate_add()
        self.update_separate_task_display()
        self.update_task_display()  # Update main window too

    def cancel_separate_add(self):
        """Cancel adding task in separate window"""
        self.separate_task_var.set("")
        self.separate_pomodoro_var.set(1)
        self.hide_separate_add_widgets()

    def update_separate_task_display(self):
        """Update task display in separate window"""
        if not hasattr(self, "separate_tasks_display"):
            return

        # Clear existing
        for widget in self.separate_tasks_display.winfo_children():
            widget.destroy()

        # Get tasks and update stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        if stats["total"] > 0:
            completion_rate = int(stats["completion_rate"])
            stats_text = f"{stats['completed']}/{stats['total']} tasks ({completion_rate}%) | 🍅 {stats['total_pomodoros_completed']}/{stats['total_pomodoros_planned']}"
            self.separate_stats_label.config(text=stats_text)
        else:
            self.separate_stats_label.config(text="No tasks yet")

        # Display tasks
        if not tasks:
            placeholder = tk.Label(
                self.separate_tasks_display,
                text="🎯 No tasks yet!\nAdd your first task above",
                font=("Arial", 11, "italic"),
                fg="#666666",
                bg="#2b2b2b",
                justify="center",
            )
            placeholder.grid(row=0, column=0, pady=20)
        else:
            for i, task in enumerate(tasks):
                self.create_separate_task_row(self.separate_tasks_display, task, i)

    def create_separate_task_row(self, parent, task, row):
        """Create task row in separate window"""
        task_row = ttk.Frame(parent)
        task_row.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2, padx=5)
        task_row.grid_columnconfigure(1, weight=1)

        # Checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_row,
            variable=completed_var,
            command=lambda: self.toggle_separate_task(task, completed_var),
        )
        check.grid(row=0, column=0, padx=(0, 8))

        # Title
        title_text = f"✅ {task.title}" if task.completed else task.title
        text_color = "#666666" if task.completed else "#00ff00"

        title_label = tk.Label(
            task_row,
            text=title_text,
            font=("Arial", 10),
            fg=text_color,
            bg="#2b2b2b",
            anchor="w",
        )
        title_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # Pomodoro info
        pomodoro_text = f"🍅{task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_label = tk.Label(
            task_row,
            text=pomodoro_text,
            font=("Arial", 9),
            fg="#00ff00",
            bg="#2b2b2b",
        )
        pomodoro_label.grid(row=0, column=2, padx=(0, 5))

        # Pomodoro buttons (for incomplete tasks)
        if not task.completed:
            button_column = 3
            # Decrease button (only if task has completed pomodoros)
            if task.pomodoros_completed > 0:
                decrease_btn = ttk.Button(
                    task_row,
                    text="-",
                    width=2,
                    command=lambda: self.remove_pomodoro_from_separate_task(task.id),
                )
                decrease_btn.grid(row=0, column=button_column, padx=(0, 2))
                button_column += 1

            # Increase button
            increase_btn = ttk.Button(
                task_row,
                text="+",
                width=2,
                command=lambda: self.add_pomodoro_to_separate_task(task.id),
            )
            increase_btn.grid(row=0, column=button_column, padx=(0, 5))
            delete_column = button_column + 1
        else:
            delete_column = 3

        # Delete button
        del_button = ttk.Button(
            task_row,
            text="🗑",
            width=3,
            command=lambda: self.delete_separate_task(task.id),
        )
        del_button.grid(row=0, column=delete_column)

    def toggle_separate_task(self, task, var):
        """Toggle task completion in separate window"""
        self.task_manager.toggle_task_completion(task.id)
        self.update_separate_task_display()
        self.update_task_display()  # Update main window too

    def delete_separate_task(self, task_id):
        """Delete task from separate window"""
        self.task_manager.delete_task(task_id)
        self.update_separate_task_display()
        self.update_task_display()  # Update main window too

    def add_pomodoro_to_separate_task(self, task_id):
        """Add pomodoro to task in separate window"""
        self.task_manager.add_pomodoro_to_task(task_id)
        self.update_separate_task_display()
        self.update_task_display()  # Update main window too

    def remove_pomodoro_from_separate_task(self, task_id):
        """Remove pomodoro from task in separate window"""
        self.task_manager.remove_pomodoro_from_task(task_id)
        self.update_separate_task_display()
        self.update_task_display()  # Update main window too

    def start_session(self, session_type: SessionType):
        """Start a session of the specified type"""
        if session_type == SessionType.WORK:
            # If it's a work session, find the next incomplete task
            incomplete_tasks = self.task_manager.get_incomplete_tasks()
            if incomplete_tasks:
                self.current_task_id = incomplete_tasks[0].id
            else:
                self.current_task_id = None
        else:
            self.current_task_id = None  # No current task for breaks

        self.session_manager.start_session(session_type)
        self.update_button_states()
        self.update_task_display()  # Refresh display to show highlight

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
            if hasattr(self, "music_status_label"):
                self.music_status_label.config(text="♪ Music Stopped")
        else:
            if self.music.start_music():
                if hasattr(self, "music_status_label"):
                    self.music_status_label.config(text="♪ Music Playing")
            else:
                if hasattr(self, "music_status_label"):
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
            if hasattr(self, "music_status_label"):
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

        # For work sessions, allow task tracking
        if session_type == SessionType.WORK:
            self.show_work_completion_dialog(session_name, duration)
        else:
            self.show_break_completion_dialog(session_name, duration)

    def show_work_completion_dialog(self, session_name: str, duration: int):
        """Show work session completion dialog with task tracking"""
        # Get incomplete tasks
        incomplete_tasks = self.task_manager.get_incomplete_tasks()

        if incomplete_tasks:
            # Show dialog with task selection
            dialog = WorkCompletionDialog(self.root, incomplete_tasks, duration)
            self.root.wait_window(dialog.dialog)

            if dialog.result and dialog.selected_task_id:
                # Add pomodoro to the selected task
                self.task_manager.add_pomodoro_to_task(dialog.selected_task_id)
                self.update_task_display()

        # Suggest next session
        completed_work = self.session_manager.completed_work_sessions
        if completed_work % self.config.get("long_break_interval", 4) == 0:
            next_session = "Long Break"
            next_type = SessionType.LONG_BREAK
        else:
            next_session = "Short Break"
            next_type = SessionType.SHORT_BREAK

        result = messagebox.askyesno(
            "Work Session Complete! 🎉",
            f"Excellent work! You completed a {duration}-minute {session_name}.\n\n"
            f"Would you like to start a {next_session} now?",
        )

        if result:
            self.start_session(next_type)

    def show_break_completion_dialog(self, session_name: str, duration: int):
        """Show break session completion dialog"""
        result = messagebox.askyesno(
            "Break Complete! 🎉",
            f"Great! You completed a {duration}-minute {session_name}.\n\n"
            f"Ready to start a Work Session?",
        )

        if result:
            self.start_session(SessionType.WORK)

    def update_display(self):
        """Update the display with current session info"""
        info = self.session_manager.get_session_info()

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
        if hasattr(self, "session_count_label"):
            self.session_count_label.config(text=f"Sessions: {info['session_count']}")

        # Update music status
        music_status = self.music.get_status()
        if hasattr(self, "music_status_label"):
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
        try:
            self.update_display()
            self.schedule_callback(1000, self.update_loop)  # Update every second
        except:
            pass  # Ignore errors if window is being destroyed

    def on_closing(self):
        """Handle application closing"""
        if self.session_manager.state in [SessionState.RUNNING, SessionState.PAUSED]:
            result = messagebox.askyesno(
                "Close Application",
                "A session is currently active. Stop the session and close?",
            )

            if result:
                self.cleanup_callbacks()
                self.save_window_dimensions()
                self.session_manager.cleanup()
                self.music.cleanup()
                self.root.destroy()
        else:
            self.cleanup_callbacks()
            self.save_window_dimensions()
            self.session_manager.cleanup()
            self.music.cleanup()
            self.root.destroy()

    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
            print("GUI mainloop finished.")
        except Exception as e:
            print(f"[X] Error in GUI mainloop: {e}")
            import traceback

            traceback.print_exc()
            raise

    def schedule_callback(self, delay, callback):
        """Schedule a callback and store its ID for proper cleanup"""
        try:
            callback_id = self.root.after(delay, callback)
            self.scheduled_callbacks.append(callback_id)
            return callback_id
        except:
            return None

    def cleanup_callbacks(self):
        """Cancel all scheduled callbacks to prevent threading errors"""
        for callback_id in self.scheduled_callbacks:
            try:
                self.root.after_cancel(callback_id)
            except:
                pass
        self.scheduled_callbacks.clear()


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
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)

        self.dialog.transient(parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.create_timer_tab(notebook)
        self.create_music_tab(notebook)
        self.create_notifications_tab(notebook)
        self.create_theme_tab(notebook)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="Save", command=self.save_application_settings
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(
            side=tk.LEFT, padx=5
        )

    def create_timer_tab(self, notebook):
        """Create timer settings tab"""
        tab = ttk.Frame(notebook, padding="10")
        notebook.add(tab, text="Timer")

        ttk.Label(tab, text="Work Duration (minutes):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.work_mins = tk.StringVar(value=self.config.get("work_mins"))
        ttk.Entry(tab, textvariable=self.work_mins).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(tab, text="Short Break (minutes):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.short_break_mins = tk.StringVar(value=self.config.get("short_break_mins"))
        ttk.Entry(tab, textvariable=self.short_break_mins).grid(
            row=1, column=1, sticky=tk.W
        )

        ttk.Label(tab, text="Long Break (minutes):").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.long_break_mins = tk.StringVar(value=self.config.get("long_break_mins"))
        ttk.Entry(tab, textvariable=self.long_break_mins).grid(
            row=2, column=1, sticky=tk.W
        )

        ttk.Label(tab, text="Long Break Interval:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self.long_break_interval = tk.StringVar(
            value=self.config.get("long_break_interval")
        )
        ttk.Entry(tab, textvariable=self.long_break_interval).grid(
            row=3, column=1, sticky=tk.W
        )

    def create_music_tab(self, notebook):
        """Create music settings tab"""
        tab = ttk.Frame(notebook, padding="10")
        notebook.add(tab, text="Music")

        ttk.Label(tab, text="MPV Executable Path:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.mpv_executable = tk.StringVar(value=self.config.get("mpv_executable"))
        ttk.Entry(tab, textvariable=self.mpv_executable, width=40).grid(
            row=0, column=1, sticky=tk.W
        )

        ttk.Label(tab, text="Default Playlist Path:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.default_playlist = tk.StringVar(
            value=self.config.get("classical_music_default_playlist")
        )
        ttk.Entry(tab, textvariable=self.default_playlist, width=40).grid(
            row=1, column=1, sticky=tk.W
        )

        ttk.Label(tab, text="Music Directory:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.music_directory = tk.StringVar(
            value=self.config.get("classical_music_playlist_dir")
        )
        ttk.Entry(tab, textvariable=self.music_directory, width=40).grid(
            row=2, column=1, sticky=tk.W
        )

    def create_notifications_tab(self, notebook):
        """Create notifications settings tab"""
        tab = ttk.Frame(notebook, padding="10")
        notebook.add(tab, text="Notifications")

        self.notify = tk.BooleanVar(value=self.config.get("notify"))
        ttk.Checkbutton(tab, text="Enable Notifications", variable=self.notify).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        self.desktop_notifications = tk.BooleanVar(
            value=self.config.get("desktop_notifications")
        )
        ttk.Checkbutton(
            tab,
            text="Enable Desktop Notifications",
            variable=self.desktop_notifications,
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

    def create_theme_tab(self, notebook):
        """Create theme settings tab"""
        tab = ttk.Frame(notebook, padding="10")
        notebook.add(tab, text="Theme")

        self.dark_theme = tk.BooleanVar(value=self.config.get("dark_theme"))
        ttk.Checkbutton(tab, text="Enable Dark Theme", variable=self.dark_theme).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5
        )

        ttk.Label(tab, text="Accent Color:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.accent_color = tk.StringVar(value=self.config.get("accent_color"))
        ttk.Entry(tab, textvariable=self.accent_color).grid(
            row=1, column=1, sticky=tk.W
        )

    def save_application_settings(self):
        """Save all settings to config file"""
        try:
            # Timer settings
            self.config.set("work_mins", int(self.work_mins.get()))
            self.config.set("short_break_mins", int(self.short_break_mins.get()))
            self.config.set("long_break_mins", int(self.long_break_mins.get()))
            self.config.set("long_break_interval", int(self.long_break_interval.get()))

            # Music settings
            self.config.set("mpv_executable", self.mpv_executable.get())
            self.config.set(
                "classical_music_default_playlist", self.default_playlist.get()
            )
            self.config.set("classical_music_playlist_dir", self.music_directory.get())

            # Notification settings
            self.config.set("notify", self.notify.get())
            self.config.set("desktop_notifications", self.desktop_notifications.get())

            # Theme settings
            self.config.set("dark_theme", self.dark_theme.get())
            self.config.set("accent_color", self.accent_color.get())

            if self.config.save_config():
                messagebox.showinfo(
                    "Settings Saved",
                    "Settings saved successfully. Please restart the application for all changes to take effect.",
                )
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save settings.")

        except ValueError:
            messagebox.showerror(
                "Invalid Input", "Please enter valid numbers for durations."
            )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def cancel(self):
        """Cancel settings changes"""
        self.dialog.destroy()

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


class WorkCompletionDialog:
    """Dialog for selecting which task a completed work session contributed to"""

    def __init__(self, parent, tasks, duration):
        """Initialize the work completion dialog"""
        self.tasks = tasks
        self.duration = duration
        self.result = False
        self.selected_task_id = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🎉 Work Session Complete!")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.center_dialog(parent)

        # Create widgets
        self.create_widgets()

    def center_dialog(self, parent):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Calculate dialog position
        dialog_width = 400
        dialog_height = 300
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"🎉 Completed {self.duration}-minute work session!",
            font=("Arial", 12, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Instruction
        instruction_label = ttk.Label(
            main_frame, text="Which task were you working on?", font=("Arial", 10)
        )
        instruction_label.grid(row=1, column=0, pady=(0, 15), sticky=tk.W)

        # Tasks frame with scrolling
        tasks_frame = ttk.LabelFrame(main_frame, text="Select Task", padding="5")
        tasks_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        tasks_frame.grid_columnconfigure(0, weight=1)

        # Task selection variable
        self.task_var = tk.StringVar()

        # Create radio buttons for each task
        for i, task in enumerate(self.tasks):
            task_text = (
                f"🍅 {task.title} ({task.pomodoros_completed}/{task.pomodoros_planned})"
            )
            radio = ttk.Radiobutton(
                tasks_frame, text=task_text, variable=self.task_var, value=task.id
            )
            radio.grid(row=i, column=0, sticky=tk.W, pady=2)

            # Select first task by default
            if i == 0:
                self.task_var.set(task.id)

        # If no tasks, show message
        if not self.tasks:
            no_tasks_label = ttk.Label(
                tasks_frame,
                text="No tasks available. Session recorded without task tracking.",
                font=("Arial", 9, "italic"),
            )
            no_tasks_label.grid(row=0, column=0, pady=10)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))

        # Buttons
        if self.tasks:
            save_button = ttk.Button(
                button_frame, text="✅ Add to Task", command=self.add_to_task
            )
            save_button.grid(row=0, column=0, padx=(0, 5))

        skip_button = ttk.Button(
            button_frame, text="⏭️ Skip Task Tracking", command=self.skip_tracking
        )
        skip_button.grid(row=0, column=1 if self.tasks else 0)

        # Bind Enter key
        self.dialog.bind(
            "<Return>",
            lambda e: self.add_to_task() if self.tasks else self.skip_tracking(),
        )
        self.dialog.bind("<Escape>", lambda e: self.skip_tracking())

    def add_to_task(self):
        """Add the completed session to the selected task"""
        if self.tasks and self.task_var.get():
            self.selected_task_id = self.task_var.get()
            self.result = True
        self.dialog.destroy()

    def skip_tracking(self):
        """Skip task tracking for this session"""
        self.result = True
        self.dialog.destroy()
