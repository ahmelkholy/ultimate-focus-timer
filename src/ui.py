#!/usr/bin/env python3
"""
ui.py - Presentation layer for Ultimate Focus Timer.
Combines: focus_app, focus_gui, dashboard, inline_task_widget, task_dialog
"""

import argparse
import csv
import importlib.util
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .core import (
    ConfigManager,
    SessionManager,
    SessionState,
    SessionType,
    Task,
    TaskManager,
)
from .daemon_manager import DaemonManager
from .google_integration import (
    DEFAULT_TASK_LIST_ID,
    GOOGLE_OAUTH_SETUP_URL,
    GOOGLE_TASKS_API_OVERVIEW_URL,
    create_google_integration,
)
from .system import (
    EXPORTS_DIR,
    SESSION_LOG_FILE,
    HotkeyManager,
    MusicController,
    NotificationManager,
    TrayManager,
)

logger = logging.getLogger(__name__)

# Set style for better visualizations
try:
    import matplotlib

    try:
        matplotlib.use("TkAgg")
    except Exception:
        matplotlib.use("Agg")
    plt.style.use("seaborn-v0_8")
    sns.set_palette("husl")
except Exception as e:
    logger.warning("Could not set matplotlib style: %s", e)

try:
    from .focus_console import ConsoleInterface
except ImportError:
    ConsoleInterface = None  # type: ignore[assignment,misc]


class TaskInputDialog:
    """Dialog for inputting daily tasks"""

    def __init__(
        self,
        parent,
        task_manager: TaskManager,
        on_tasks_updated: Optional[Callable] = None,
    ):
        """Initialize the task input dialog"""
        self.parent = parent
        self.task_manager = task_manager
        self.on_tasks_updated = on_tasks_updated
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📝 Daily Tasks")
        self.dialog.geometry("500x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.center_dialog()

        # Create widgets
        self.create_widgets()

        # Focus on the first entry
        if hasattr(self, "task_entries") and self.task_entries:
            self.task_entries[0]["title"].focus()

    def center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Calculate dialog position
        dialog_width = 500
        dialog_height = 400
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

    def create_widgets(self):
        """Create and layout dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.dialog.grid_rowconfigure(0, weight=1)
        self.dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="📝 What are you working on?",
            font=("Arial", 14, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Existing tasks frame (if any)
        existing_tasks = self.task_manager.get_today_tasks()
        if existing_tasks:
            existing_frame = ttk.LabelFrame(
                main_frame, text="Current Tasks", padding="5"
            )
            existing_frame.grid(
                row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
            )
            existing_frame.grid_columnconfigure(0, weight=1)

            # Create scrollable frame for existing tasks
            canvas = tk.Canvas(existing_frame, height=100)
            scrollbar = ttk.Scrollbar(
                existing_frame, orient="vertical", command=canvas.yview
            )
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

            # Display existing tasks
            for i, task in enumerate(existing_tasks):
                task_frame = ttk.Frame(scrollable_frame)
                task_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
                task_frame.grid_columnconfigure(1, weight=1)

                # Checkbox for completion
                completed_var = tk.BooleanVar(value=task.completed)
                completed_check = ttk.Checkbutton(
                    task_frame,
                    variable=completed_var,
                    command=lambda t=task, v=completed_var: self.toggle_task_completion(
                        t, v
                    ),
                )
                completed_check.grid(row=0, column=0, padx=(0, 5))

                # Task title
                title_text = task.title
                if task.completed:
                    title_text = f"✅ {title_text}"

                task_label = ttk.Label(
                    task_frame,
                    text=title_text,
                    font=("Arial", 12),
                    foreground="gray" if task.completed else "black",
                )
                task_label.grid(row=0, column=1, sticky=tk.W)

                # Pomodoro count
                pomodoro_text = (
                    f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
                )
                pomodoro_label = ttk.Label(
                    task_frame, text=pomodoro_text, font=("Arial", 11)
                )
                pomodoro_label.grid(row=0, column=2, padx=(5, 0))

        # New tasks frame
        new_tasks_frame = ttk.LabelFrame(main_frame, text="Add New Tasks", padding="5")
        new_tasks_frame.grid(
            row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10)
        )
        new_tasks_frame.grid_columnconfigure(0, weight=1)

        # Task entries
        self.task_entries = []
        for i in range(5):  # Allow adding up to 5 new tasks
            self.add_task_entry(new_tasks_frame, i)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        # Buttons
        save_button = ttk.Button(
            button_frame,
            text="💾 Save Tasks",
            command=self.save_tasks,
            style="Accent.TButton",
        )
        save_button.grid(row=0, column=0, padx=(0, 5))

        cancel_button = ttk.Button(button_frame, text="❌ Cancel", command=self.cancel)
        cancel_button.grid(row=0, column=1, padx=(5, 0))

        # Skip button (for users who don't want to add tasks)
        skip_button = ttk.Button(
            button_frame, text="⏭️ Skip for Today", command=self.skip_for_today
        )
        skip_button.grid(row=0, column=2, padx=(10, 0))

        # Bind Enter key to save
        self.dialog.bind("<Return>", lambda e: self.save_tasks())
        self.dialog.bind("<Escape>", lambda e: self.cancel())

    def add_task_entry(self, parent, row):
        """Add a task entry row"""
        task_frame = ttk.Frame(parent)
        task_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2)
        task_frame.grid_columnconfigure(1, weight=1)

        # Task number label
        number_label = ttk.Label(task_frame, text=f"{row + 1}.")
        number_label.grid(row=0, column=0, padx=(0, 5))

        # Task title entry
        title_var = tk.StringVar()
        title_entry = ttk.Entry(task_frame, textvariable=title_var, width=30)
        title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        # Pomodoros spinbox
        pomodoros_var = tk.IntVar(value=1)
        pomodoros_label = ttk.Label(task_frame, text="🍅")
        pomodoros_label.grid(row=0, column=2, padx=(0, 2))

        pomodoros_spinbox = ttk.Spinbox(
            task_frame, from_=1, to=10, width=5, textvariable=pomodoros_var
        )
        pomodoros_spinbox.grid(row=0, column=3)

        # Store entry references
        entry_data = {
            "title": title_entry,
            "title_var": title_var,
            "pomodoros_var": pomodoros_var,
        }
        self.task_entries.append(entry_data)

    def toggle_task_completion(self, task: Task, var: tk.BooleanVar):
        """Toggle task completion status"""
        if var.get():
            self.task_manager.complete_task(task.id)
        else:
            self.task_manager.uncomplete_task(task.id)

        if self.on_tasks_updated:
            self.on_tasks_updated()

    def save_tasks(self):
        """Save new tasks and close dialog"""
        new_tasks_added = False

        for entry in self.task_entries:
            title = entry["title_var"].get().strip()
            if title:  # Only create tasks with non-empty titles
                pomodoros = entry["pomodoros_var"].get()
                self.task_manager.add_task(title, pomodoros_planned=pomodoros)
                new_tasks_added = True

        if new_tasks_added and self.on_tasks_updated:
            self.on_tasks_updated()

        self.result = "saved"
        self.dialog.destroy()

    def cancel(self):
        """Cancel dialog without saving"""
        self.result = "cancelled"
        self.dialog.destroy()

    def skip_for_today(self):
        """Skip task planning for today"""
        self.result = "skipped"
        self.dialog.destroy()


class TaskDisplayWidget:
    """Widget for displaying tasks in the main GUI"""

    def __init__(self, parent, task_manager: TaskManager):
        """Initialize task display widget"""
        self.parent = parent
        self.task_manager = task_manager

        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="📝 Current Tasks", padding="5")
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        """Create task display widgets"""
        # Configure grid
        self.frame.grid_columnconfigure(0, weight=1)

        # Header frame
        header_frame = ttk.Frame(self.frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Stats label
        self.stats_label = ttk.Label(header_frame, text="", font=("Arial", 10))
        self.stats_label.grid(row=0, column=0, sticky=tk.W)

        # Manage tasks button
        manage_button = ttk.Button(
            header_frame, text="⚙️ Manage", command=self.open_task_dialog, width=10
        )
        manage_button.grid(row=0, column=2, sticky=tk.E)

        # Tasks container frame with scrolling
        self.tasks_container = ttk.Frame(self.frame)
        self.tasks_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.tasks_container.grid_columnconfigure(0, weight=1)

        # Set frame to expand
        self.frame.grid_rowconfigure(1, weight=1)

    def update_display(self):
        """Update the task display"""
        # Clear existing tasks
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

        # Get tasks and stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        # Update stats label
        if stats["total"] > 0:
            stats_text = (
                f"Tasks: {stats['completed']}/{stats['total']} | "
                f"Pomodoros: {stats['total_pomodoros_completed']}/"
                f"{stats['total_pomodoros_planned']}"
            )
            self.stats_label.config(text=stats_text)
        else:
            self.stats_label.config(text="No active tasks")

        # Display tasks
        if not tasks:
            no_tasks_label = ttk.Label(
                self.tasks_container,
                text="Click 'Manage' to add your first task! 🎯",
                font=("Arial", 11, "italic"),
            )
            no_tasks_label.grid(row=0, column=0, pady=10)
        else:
            for i, task in enumerate(tasks):
                self.create_task_row(self.tasks_container, task, i)

    def create_task_row(self, parent, task: Task, row: int):
        """Create a row for displaying a task"""
        task_frame = ttk.Frame(parent)
        task_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=1)
        task_frame.grid_columnconfigure(1, weight=1)

        # Completion checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_frame,
            variable=completed_var,
            command=lambda: self.toggle_task(task, completed_var),
        )
        check.grid(row=0, column=0, padx=(0, 5))

        # Task title
        title_text = task.title
        if task.completed:
            title_text = f"✅ {title_text}"

        title_label = ttk.Label(
            task_frame,
            text=title_text,
            font=("Arial", 12),
            foreground="gray" if task.completed else "black",
        )
        title_label.grid(row=0, column=1, sticky=tk.W)

        # Pomodoro progress
        pomodoro_text = f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_label = ttk.Label(task_frame, text=pomodoro_text, font=("Arial", 11))
        pomodoro_label.grid(row=0, column=2, padx=(5, 0))

    def toggle_task(self, task: Task, var: tk.BooleanVar):
        """Toggle task completion"""
        if var.get():
            self.task_manager.complete_task(task.id)
        else:
            self.task_manager.uncomplete_task(task.id)

        self.update_display()

    def open_task_dialog(self):
        """Open task management dialog"""
        dialog = TaskInputDialog(
            self.parent, self.task_manager, on_tasks_updated=self.update_display
        )
        self.parent.wait_window(dialog.dialog)

    def get_frame(self):
        """Get the main frame widget"""
        return self.frame


class InlineTaskWidget:
    """Inline task management widget for the main GUI"""

    def __init__(self, parent, task_manager: TaskManager):
        """Initialize the inline task widget"""
        self.parent = parent
        self.task_manager = task_manager
        self.adding_task = False
        self.typing_active = False

        # Drag and drop state
        self.drag_source = None
        self.drag_start_y = 0
        self.task_rows = []  # List of (task, frame) tuples for vim navigation
        self.selected_row_index = -1  # Currently selected row for vim navigation

        # Create main frame with dark styling
        self.frame = ttk.LabelFrame(parent, text="📝 Current Tasks", padding="8")
        self.create_widgets()
        self.apply_dark_theme()
        self.setup_vim_keybindings()
        self.update_display()

    def create_widgets(self):
        """Create task management widgets"""
        # Configure grid
        self.frame.grid_columnconfigure(0, weight=1)

        # Header frame with stats and add button
        header_frame = ttk.Frame(self.frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        header_frame.grid_columnconfigure(0, weight=1)

        # Stats label with dark theme
        self.stats_label = tk.Label(
            header_frame,
            text="",
            font=("Arial", 10),
            fg="#00ff00",  # Bright green
            bg="#2b2b2b",  # Dark background
        )
        self.stats_label.grid(row=0, column=0, sticky=tk.W)

        # Add task button
        self.add_button = ttk.Button(
            header_frame,
            text="➕ Add Task (T)",
            command=self.show_add_task_entry,
            width=15,
            style="TaskWidget.TButton",
        )
        self.add_button.grid(row=0, column=1, sticky=tk.E)

        # Add task entry frame (initially hidden but space reserved)
        self.add_task_frame = ttk.Frame(self.frame, height=35)  # Reserve space
        self.add_task_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 8)
        )
        self.add_task_frame.grid_columnconfigure(0, weight=1)
        self.add_task_frame.grid_propagate(False)  # Don't shrink when empty

        # Task entry
        self.task_entry_var = tk.StringVar()
        self.task_entry = ttk.Entry(
            self.add_task_frame,
            textvariable=self.task_entry_var,
            style="TaskWidget.TEntry",
        )
        self.task_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # Bind focus events to enable/disable shortcuts and change text color
        self.task_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.task_entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.task_entry.bind("<KeyPress>", self.on_entry_key_press)

        # Pomodoro count
        self.pomodoro_var = tk.IntVar(value=1)
        pomodoro_label = ttk.Label(self.add_task_frame, text="🍅")
        pomodoro_label.grid(row=0, column=1, padx=(0, 2))

        self.pomodoro_spinbox = ttk.Spinbox(
            self.add_task_frame,
            from_=1,
            to=10,
            width=3,
            textvariable=self.pomodoro_var,
            style="TaskWidget.TSpinbox",
        )
        self.pomodoro_spinbox.grid(row=0, column=2, padx=(0, 5))

        # Save/Cancel buttons
        save_button = ttk.Button(
            self.add_task_frame,
            text="✓",
            command=self.save_new_task,
            width=3,
            style="TaskWidget.TButton",
        )
        save_button.grid(row=0, column=3, padx=(0, 2))

        cancel_button = ttk.Button(
            self.add_task_frame,
            text="✗",
            command=self.cancel_add_task,
            width=3,
            style="TaskWidget.TButton",
        )
        cancel_button.grid(row=0, column=4)

        # Hide add task widgets initially (but keep frame space)
        for widget in self.add_task_frame.winfo_children():
            widget.grid_remove()

        # Tasks container with fixed height and scrolling - FIXED SIZE
        self.tasks_canvas = tk.Canvas(
            self.frame, height=120, highlightthickness=0, bg="#2b2b2b"
        )
        tasks_scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tasks_canvas.yview
        )
        self.tasks_container = ttk.Frame(self.tasks_canvas)

        self.tasks_container.bind(
            "<Configure>",
            lambda e: self.tasks_canvas.configure(
                scrollregion=self.tasks_canvas.bbox("all")
            ),
        )

        # Store canvas window ID for width updates
        self.canvas_window_id = self.tasks_canvas.create_window(
            (0, 0), window=self.tasks_container, anchor="nw"
        )
        self.tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)

        # Grid the canvas and scrollbar - span both columns for full width
        self.tasks_canvas.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5)
        )
        tasks_scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=(0, 5))

        # Configure for full width expansion
        self.frame.grid_columnconfigure(0, weight=1)
        self.tasks_container.grid_columnconfigure(0, weight=1)

        # Bind canvas resize to update scroll region and task width
        self.tasks_canvas.bind("<Configure>", self.on_canvas_configure)

        # Bind Enter key to save
        self.task_entry.bind("<Return>", lambda e: self.save_new_task())
        self.task_entry.bind("<Escape>", lambda e: self.cancel_add_task())

    def setup_vim_keybindings(self):
        """Setup vim-style keybindings for task navigation"""
        # Bind to the frame and canvas for vim navigation
        self.frame.bind(
            "<j>",
            lambda e: self.vim_navigate_down() if not self.typing_active else None,
        )
        self.frame.bind(
            "<k>", lambda e: self.vim_navigate_up() if not self.typing_active else None
        )
        self.frame.bind(
            "<d>",
            lambda e: self.vim_delete_selected() if not self.typing_active else None,
        )
        self.frame.bind(
            "<g>", lambda e: self.vim_goto_first() if not self.typing_active else None
        )
        self.frame.bind(
            "<G>", lambda e: self.vim_goto_last() if not self.typing_active else None
        )
        self.frame.bind(
            "<i>",
            lambda e: self.show_add_task_entry() if not self.typing_active else None,
        )
        self.frame.bind(
            "<a>",
            lambda e: self.show_add_task_entry() if not self.typing_active else None,
        )
        self.frame.bind(
            "<space>",
            lambda e: self.vim_toggle_selected() if not self.typing_active else None,
        )
        self.frame.bind(
            "<t>",
            lambda e: self.vim_delegate_tomorrow() if not self.typing_active else None,
        )
        self.frame.bind(
            "<w>",
            lambda e: self.vim_delegate_next_week() if not self.typing_active else None,
        )

        # Make frame focusable
        self.frame.config(takefocus=1)
        self.tasks_canvas.config(takefocus=1)

    def vim_navigate_down(self):
        """Navigate down in task list (vim j key)"""
        if not self.task_rows:
            return

        # Clear previous selection
        if 0 <= self.selected_row_index < len(self.task_rows):
            _, frame = self.task_rows[self.selected_row_index]
            frame.configure(style="TFrame")

        # Move to next row
        self.selected_row_index = (self.selected_row_index + 1) % len(self.task_rows)

        # Highlight new selection
        _, frame = self.task_rows[self.selected_row_index]
        frame.configure(style="Selected.TFrame")

        # Scroll to make visible
        self._scroll_to_selected()

    def vim_navigate_up(self):
        """Navigate up in task list (vim k key)"""
        if not self.task_rows:
            return

        # Clear previous selection
        if 0 <= self.selected_row_index < len(self.task_rows):
            _, frame = self.task_rows[self.selected_row_index]
            frame.configure(style="TFrame")

        # Move to previous row
        self.selected_row_index = (self.selected_row_index - 1) % len(self.task_rows)

        # Highlight new selection
        _, frame = self.task_rows[self.selected_row_index]
        frame.configure(style="Selected.TFrame")

        # Scroll to make visible
        self._scroll_to_selected()

    def vim_delete_selected(self):
        """Delete selected task (vim dd keys)"""
        if 0 <= self.selected_row_index < len(self.task_rows):
            task, _ = self.task_rows[self.selected_row_index]
            self.delete_task(task)

    def vim_goto_first(self):
        """Go to first task (vim g key)"""
        if not self.task_rows:
            return

        # Clear previous selection
        if 0 <= self.selected_row_index < len(self.task_rows):
            _, frame = self.task_rows[self.selected_row_index]
            frame.configure(style="TFrame")

        # Go to first
        self.selected_row_index = 0

        # Highlight new selection
        _, frame = self.task_rows[self.selected_row_index]
        frame.configure(style="Selected.TFrame")

        # Scroll to make visible
        self._scroll_to_selected()

    def vim_goto_last(self):
        """Go to last task (vim G key)"""
        if not self.task_rows:
            return

        # Clear previous selection
        if 0 <= self.selected_row_index < len(self.task_rows):
            _, frame = self.task_rows[self.selected_row_index]
            frame.configure(style="TFrame")

        # Go to last
        self.selected_row_index = len(self.task_rows) - 1

        # Highlight new selection
        _, frame = self.task_rows[self.selected_row_index]
        frame.configure(style="Selected.TFrame")

        # Scroll to make visible
        self._scroll_to_selected()

    def vim_toggle_selected(self):
        """Toggle completion of selected task (vim space key)"""
        if 0 <= self.selected_row_index < len(self.task_rows):
            task, _ = self.task_rows[self.selected_row_index]
            if task.completed:
                self.task_manager.uncomplete_task(task.id)
            else:
                self.task_manager.complete_task(task.id)
            self.update_display()

    def vim_delegate_tomorrow(self):
        """Delegate selected task to tomorrow (vim t key)"""
        if 0 <= self.selected_row_index < len(self.task_rows):
            task, _ = self.task_rows[self.selected_row_index]
            from datetime import datetime, timedelta

            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            task.description = f"[Delegated to {tomorrow}] {task.description}"
            task.touch()
            self.task_manager.save_tasks()
            logger.info(f"Task '{task.title}' delegated to tomorrow")
            self.update_display()

    def vim_delegate_next_week(self):
        """Delegate selected task to next week (vim w key)"""
        if 0 <= self.selected_row_index < len(self.task_rows):
            task, _ = self.task_rows[self.selected_row_index]
            from datetime import datetime, timedelta

            next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            task.description = f"[Delegated to {next_week}] {task.description}"
            task.touch()
            self.task_manager.save_tasks()
            logger.info(f"Task '{task.title}' delegated to next week")
            self.update_display()

    def _scroll_to_selected(self):
        """Scroll canvas to make selected task visible"""
        if 0 <= self.selected_row_index < len(self.task_rows):
            _, frame = self.task_rows[self.selected_row_index]
            # Get frame position
            self.tasks_canvas.update_idletasks()
            bbox = self.tasks_canvas.bbox("all")
            if bbox:
                frame_y = frame.winfo_y()
                frame_height = frame.winfo_height()
                canvas_height = self.tasks_canvas.winfo_height()

                # Calculate scroll position
                scroll_top = frame_y / bbox[3] if bbox[3] > 0 else 0
                scroll_bottom = (frame_y + frame_height) / bbox[3] if bbox[3] > 0 else 0

                # Scroll if not fully visible
                current_top = self.tasks_canvas.yview()[0]
                current_bottom = self.tasks_canvas.yview()[1]

                if scroll_top < current_top:
                    self.tasks_canvas.yview_moveto(scroll_top)
                elif scroll_bottom > current_bottom:
                    self.tasks_canvas.yview_moveto(
                        scroll_bottom - (canvas_height / bbox[3])
                    )

    def apply_dark_theme(self):
        """Apply dark theme to the task widget"""
        try:
            # Configure the main frame and canvas for dark theme
            style = ttk.Style()

            # Configure dark colors
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            accent_color = "#00ff00"
            button_color = "#404040"

            # Apply dark theme to TTK widgets
            style.configure(
                "TaskWidget.TLabelframe",
                background=bg_color,
                foreground=fg_color,
                borderwidth=1,
            )
            style.configure(
                "TaskWidget.TLabelframe.Label",
                background=bg_color,
                foreground=accent_color,
                font=("Arial", 10, "bold"),
            )

            # Configure buttons for dark theme
            style.configure(
                "TaskWidget.TButton",
                background=button_color,
                foreground=fg_color,
                borderwidth=1,
                focuscolor=accent_color,
            )
            style.map(
                "TaskWidget.TButton",
                background=[("active", accent_color), ("pressed", "#006600")],
            )

            # Configure entry widgets
            style.configure(
                "TaskWidget.TEntry",
                background=button_color,
                foreground=fg_color,
                borderwidth=1,
                insertcolor=fg_color,
            )

            # Configure spinbox
            style.configure(
                "TaskWidget.TSpinbox",
                background=button_color,
                foreground=fg_color,
                borderwidth=1,
                arrowcolor=fg_color,
            )

            # Configure checkbutton
            style.configure(
                "TaskWidget.TCheckbutton",
                background=bg_color,
                foreground=fg_color,
                indicatorcolor=button_color,
                focuscolor=accent_color,
            )

            # Configure selected row style for vim navigation
            style.configure(
                "Selected.TFrame",
                background="#4a4a4a",
                relief="solid",
                borderwidth=2,
            )

            # Configure the frame
            self.frame.configure(style="TaskWidget.TLabelframe")

            # Configure canvas background
            if hasattr(self, "tasks_canvas"):
                self.tasks_canvas.configure(bg=bg_color)

        except Exception as e:
            # Fallback if theming fails
            print(f"Dark theme application failed: {e}")

    def show_add_task_entry(self):
        """Show the add task entry without changing layout"""
        if not self.adding_task:
            self.adding_task = True
            self.typing_active = True  # Set typing state immediately

            # Show all widgets in the frame
            for widget in self.add_task_frame.winfo_children():
                widget.grid()

            self.add_button.config(state="disabled")

            # Focus on entry after a short delay to ensure it's visible
            self.task_entry.after(10, self._focus_entry)

            self.task_entry_var.set("")
            self.pomodoro_var.set(1)
            # Update display to hide placeholder text when typing
            self.update_display()

    def _focus_entry(self):
        """Helper method to focus the entry field"""
        try:
            self.task_entry.focus_set()
            self.task_entry.select_range(0, tk.END)
        except Exception:
            pass  # Ignore focus errors

    def save_new_task(self):
        """Save the new task"""
        task_text = self.task_entry_var.get().strip()
        if task_text:
            pomodoros = self.pomodoro_var.get()
            self.task_manager.add_task(task_text, pomodoros_planned=pomodoros)
            self.update_display()

        self.cancel_add_task()

    def cancel_add_task(self):
        """Cancel adding new task and clear the frame"""
        self.adding_task = False
        self.typing_active = False  # Explicitly reset typing state

        # Clear the entry fields
        self.task_entry_var.set("")
        self.pomodoro_var.set(1)

        # Hide all widgets in the frame instead of removing the frame
        for widget in self.add_task_frame.winfo_children():
            widget.grid_remove()

        self.add_button.config(state="normal")

        # Return focus to main window to ensure shortcuts work
        self._return_focus_to_main()

        # Update display to show placeholder text again if no tasks
        self.update_display()

    def update_display(self):
        """Update the task display"""
        # Clear existing tasks
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

        # Clear task rows list
        self.task_rows = []

        # Get tasks and stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        # Update stats label
        if stats["total"] > 0:
            completion_rate = int(stats["completion_rate"])
            stats_text = (
                f"Progress: {stats['completed']}/{stats['total']} tasks "
                f"({completion_rate}%) | 🍅 "
                f"{stats['total_pomodoros_completed']}/"
                f"{stats['total_pomodoros_planned']}"
            )
            self.stats_label.config(text=stats_text)
        else:
            self.stats_label.config(text="No tasks yet - add your first task!")

        # Display tasks
        if not tasks and not self.adding_task:
            # Show placeholder when no tasks and not currently adding - DARK THEMED
            placeholder_frame = ttk.Frame(self.tasks_container)
            placeholder_frame.grid(row=0, column=0, pady=10)

            placeholder_label = tk.Label(
                placeholder_frame,
                text="🎯 Add your first task to get started!\nPress 'T' or click 'Add Task' below",
                font=("Arial", 11, "italic"),
                fg="#666666",  # Gray text
                bg="#2b2b2b",  # Dark background
                justify="center",
            )
            placeholder_label.pack()
        elif tasks:
            # Show tasks and populate task_rows
            for i, task in enumerate(tasks):
                task_frame = self.create_task_row(self.tasks_container, task, i)
                self.task_rows.append((task, task_frame))

    def on_canvas_configure(self, event):
        """Handle canvas resize to update task container width"""
        # Set the width of the tasks_container to match the canvas width
        canvas_width = event.width
        if hasattr(self, "canvas_window_id"):
            self.tasks_canvas.itemconfig(self.canvas_window_id, width=canvas_width)

    def create_task_row(self, parent, task: Task, row: int):
        """Create a row for displaying a task with drag-and-drop support"""
        task_frame = ttk.Frame(parent)
        task_frame.grid(
            row=row, column=0, sticky=(tk.W, tk.E), pady=1, padx=0
        )  # Remove padding to maximize width

        # Configure the task frame to fill available width
        parent.grid_columnconfigure(0, weight=1)  # Ensure parent expands column 0
        task_frame.grid_columnconfigure(
            2, weight=1
        )  # Make title column expand to fill space

        # Determine selection background for this row
        idx = row
        sel_bg = (
            "#1a3a1a" if idx == getattr(self, "selected_task_index", -1) else "#2b2b2b"
        )

        # Add drag-and-drop bindings
        task_frame.bind(
            "<ButtonPress-1>", lambda e: self.on_drag_start(e, task_frame, task)
        )
        task_frame.bind("<B1-Motion>", lambda e: self.on_drag_motion(e, task_frame))
        task_frame.bind(
            "<ButtonRelease-1>", lambda e: self.on_drag_release(e, task_frame, task)
        )

        sync_state = self.task_manager.get_sync_status(task.id)
        sync_icon_map = {
            "synced": "☁",
            "pending": "…",
            "error": "⚠",
            "disabled": "⏻",
            "local": "·",
        }
        sync_color_map = {
            "synced": "#00bfff",
            "pending": "#ffaa00",
            "error": "#ff5555",
            "disabled": "#666666",
            "local": "#666666",
        }
        sync_label = tk.Label(
            task_frame,
            text=sync_icon_map.get(sync_state, "·"),
            font=("Arial", 11),
            fg=sync_color_map.get(sync_state, "#666666"),
            bg=sel_bg,
        )
        sync_label.grid(row=0, column=0, padx=(0, 2))

        # Completion checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_frame,
            variable=completed_var,
            command=lambda: self.toggle_task(task, completed_var),
        )
        check.grid(row=0, column=1, padx=(0, 4))  # Small padding after checkbox

        # Task title with green text color - MAXIMUM WIDTH
        title_text = task.title
        if task.completed:
            title_text = f"✅ {title_text}"
            text_color = "#666666"  # Gray for completed
        else:
            text_color = "#00ff00"  # Bright green for active

        title_label = tk.Label(
            task_frame,
            text=title_text,
            font=("Arial", 12),
            fg=text_color,
            bg=sel_bg,  # Dark background or selected
            anchor="w",
            justify="left",
        )
        title_label.grid(
            row=0, column=2, sticky=(tk.W, tk.E), padx=(0, 1)
        )  # Minimal padding for maximum width

        # Bind drag to title label as well
        title_label.bind(
            "<ButtonPress-1>", lambda e: self.on_drag_start(e, task_frame, task)
        )
        title_label.bind("<B1-Motion>", lambda e: self.on_drag_motion(e, task_frame))
        title_label.bind(
            "<ButtonRelease-1>", lambda e: self.on_drag_release(e, task_frame, task)
        )

        # Pomodoro progress with green color
        pomodoro_text = f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_color = "#00cc00" if task.pomodoros_completed > 0 else "#666666"

        pomodoro_label = tk.Label(
            task_frame,
            text=pomodoro_text,
            font=("Arial", 11),
            fg=pomodoro_color,
            bg=sel_bg,
        )
        pomodoro_label.grid(row=0, column=3, padx=(1, 1))  # Minimal padding

        # Pomodoro buttons (only for incomplete tasks)
        if not task.completed:
            button_column = 3
            # Decrease pomodoro button (only if task has completed pomodoros)
            if task.pomodoros_completed > 0:
                decrease_pomodoro_button = ttk.Button(
                    task_frame,
                    text="🍅-",
                    command=lambda: self.remove_pomodoro_from_task(task),
                    width=3,
                )
                decrease_pomodoro_button.grid(row=0, column=button_column, padx=(1, 1))
                button_column += 1

            # Add pomodoro button
            add_pomodoro_button = ttk.Button(
                task_frame,
                text="🍅+",
                command=lambda: self.add_pomodoro_to_task(task),
                width=3,
            )
            add_pomodoro_button.grid(row=0, column=button_column, padx=(1, 1))
            delete_column = button_column + 1
        else:
            delete_column = 3

        # Delete button
        delete_button = ttk.Button(
            task_frame, text="🗑️", command=lambda: self.delete_task(task), width=3
        )
        delete_button.grid(row=0, column=delete_column, padx=(1, 0))

        return task_frame  # Return the frame for task_rows list

    def toggle_task(self, task: Task, var: tk.BooleanVar):
        """Toggle task completion"""
        self.task_manager.toggle_task_completion(task.id)
        if var.get():
            self.show_task_completion_message(task)
        self.update_display()

    def add_pomodoro_to_task(self, task: Task):
        """Add a pomodoro to a task"""
        self.task_manager.add_pomodoro_to_task(task.id)
        self.update_display()

        # Show positive feedback
        if task.pomodoros_completed + 1 >= task.pomodoros_planned:
            self.show_task_ready_message(task)

    def remove_pomodoro_from_task(self, task: Task):
        """Remove a pomodoro from a task"""
        self.task_manager.remove_pomodoro_from_task(task.id)
        self.update_display()

    def delete_task(self, task: Task):
        """Delete a task directly without confirmation"""
        self.task_manager.delete_task(task.id)
        self.update_display()

    def delete_last_task(self):
        """Delete the most recently added task (for keyboard shortcut)"""
        tasks = self.task_manager.get_today_tasks()
        if tasks:
            # Get the most recently added task (first in the list since we insert at top)
            last_task = tasks[0]
            self.task_manager.delete_task(last_task.id)
            self.update_display()
            print(f"Deleted task: {last_task.title}")

    def show_task_completion_message(self, task: Task):
        """Show a message when task is completed"""
        if task.pomodoros_completed >= task.pomodoros_planned:
            message = f"🎉 Excellent! Task '{task.title}' completed with all planned Pomodoros!"
        else:
            message = f"✅ Task '{task.title}' marked as complete!"

        # You could show this in a status bar or as a brief popup
        # For now, we'll use the console
        print(message)

    def show_task_ready_message(self, task: Task):
        """Show message when task reaches planned pomodoros"""
        print(f"🍅 Great! Task '{task.title}' has reached its planned Pomodoros!")

    def on_drag_start(self, event, frame, task):
        """Handle drag start event"""
        self.drag_source = (frame, task)
        self.drag_start_y = event.y_root
        frame.configure(style="Selected.TFrame")

    def on_drag_motion(self, event, frame):
        """Handle drag motion event"""
        if not self.drag_source:
            return

        # Visual feedback: change cursor or frame appearance
        current_y = event.y_root
        delta_y = current_y - self.drag_start_y

        # Could add visual dragging effect here if desired
        if abs(delta_y) > 5:  # Minimum drag distance
            frame.configure(style="Selected.TFrame")

    def on_drag_release(self, event, frame, task):
        """Handle drag release event - reorder tasks"""
        if not self.drag_source:
            return

        source_frame, source_task = self.drag_source
        self.drag_source = None

        # Reset frame style
        source_frame.configure(style="TFrame")

        # Find target position based on mouse position
        target_index = self._find_drop_target(event.y_root)

        if target_index is not None:
            # Reorder tasks
            self._reorder_tasks(source_task, target_index)

    def _find_drop_target(self, y_position):
        """Find the target index for dropping based on Y position"""
        # Get all task frames and their positions
        for i, (task, frame) in enumerate(self.task_rows):
            frame_y = frame.winfo_rooty()
            frame_height = frame.winfo_height()
            frame_mid = frame_y + (frame_height / 2)

            # Check if drop position is above or below this frame's midpoint
            if y_position < frame_mid:
                return i

        # If we're below all frames, return last position
        return len(self.task_rows) - 1 if self.task_rows else 0

    def _reorder_tasks(self, source_task, target_index):
        """Reorder tasks by moving source_task to target_index"""
        today_key = self.task_manager.get_today_key()
        tasks = self.task_manager.get_today_tasks()

        # Find source index
        source_index = next(
            (i for i, t in enumerate(tasks) if t.id == source_task.id), None
        )

        if source_index is not None and source_index != target_index:
            # Remove from old position
            task_to_move = tasks.pop(source_index)

            # Insert at new position
            tasks.insert(target_index, task_to_move)

            # Update task manager's tasks list
            self.task_manager.tasks[today_key] = tasks
            self.task_manager.save_tasks()

            # Refresh display
            self.update_display()

            logger.info(
                f"Reordered task '{source_task.title}' from position {source_index} to {target_index}"
            )

    def get_frame(self):
        """Get the main frame widget"""
        return self.frame

    def trigger_add_task(self):
        """Public method to trigger adding a new task (for keyboard shortcuts)"""
        self.show_add_task_entry()

    def get_current_task_for_session(self) -> Optional[Task]:
        """Get the most suitable task for the current session"""
        incomplete_tasks = self.task_manager.get_incomplete_tasks()
        if not incomplete_tasks:
            return None

        # Prioritize tasks that need more pomodoros
        for task in incomplete_tasks:
            if task.pomodoros_completed < task.pomodoros_planned:
                return task

        # If all tasks have reached their planned pomodoros, return the first incomplete one
        return incomplete_tasks[0]

    def check_and_prompt_for_tasks(self) -> bool:
        """Check if there are tasks and prompt to add some if none exist"""
        if not self.task_manager.has_tasks_for_today():
            self.show_add_task_entry()
            return False  # Don't start session yet

        return True  # Has tasks, can proceed

    def on_entry_focus_in(self, event):
        """Handle entry focus in - change text color to green and disable shortcuts"""
        self.typing_active = True
        # Configure green text color for typing
        style = ttk.Style()
        style.configure(
            "TaskWidget.TEntry",
            background="#404040",
            foreground="#00ff00",  # Green text while typing
            borderwidth=1,
            insertcolor="#00ff00",
        )

    def on_entry_focus_out(self, event):
        """Handle entry focus out - restore normal colors and enable shortcuts"""
        # Use a small delay to ensure proper state management
        self.parent.after(50, self._handle_focus_out)

    def _handle_focus_out(self):
        """Helper method to handle focus out with proper state management"""
        # Only reset typing state if we're not actively adding a task
        if not self.adding_task:
            self.typing_active = False

        # Restore normal text color
        style = ttk.Style()
        style.configure(
            "TaskWidget.TEntry",
            background="#404040",
            foreground="#ffffff",  # White text when not typing
            borderwidth=1,
            insertcolor="#ffffff",
        )

        # Return focus to main window after a short delay to ensure shortcuts work
        if hasattr(self, "parent"):
            self.parent.after(100, self._return_focus_to_main)

    def _return_focus_to_main(self):
        """Helper method to return focus to main window"""
        try:
            # Find the root window and set focus to it
            current = self.parent
            while hasattr(current, "master") and current.master:
                current = current.master
            if hasattr(current, "focus_set"):
                current.focus_set()
        except Exception:
            pass  # Ignore any focus errors

    def on_entry_key_press(self, event):
        """Handle key press in entry - ensure typing state is active"""
        self.typing_active = True

    def is_typing(self):
        """Check if user is currently typing in the task entry"""
        # Check both the typing_active flag and if entry has focus
        typing_state = getattr(self, "typing_active", False)

        # Also check if the entry widget currently has focus
        if hasattr(self, "task_entry"):
            try:
                focused_widget = self.task_entry.focus_get()
                has_focus = focused_widget == self.task_entry
                typing_state = typing_state or has_focus
            except Exception:
                pass  # Ignore focus errors

        return typing_state


@dataclass
class SessionData:
    """Represents a single focus session"""

    timestamp: datetime
    action: str  # Started, Completed, Paused, etc.
    session_type: str  # work, short_break, long_break
    duration: int  # in minutes
    date: datetime


class SessionAnalyzer:
    """Analyzes session data and generates statistics"""

    def __init__(self, log_path: Path = None):
        self.log_path = Path(log_path) if log_path else SESSION_LOG_FILE
        self.sessions: List[SessionData] = []
        self.load_session_data()

    def load_session_data(self) -> None:
        """Load session data from log file"""
        if not self.log_path.exists():
            logger.warning("Log file not found: %s", self.log_path)
            return

        pattern = (
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - "
            r"(Started|Completed|Paused|Resumed) (\w+) session.*?(\d+) minutes"
        )

        try:
            with open(self.log_path, "r", encoding="utf-8") as file:
                for line in file:
                    match = re.search(pattern, line)
                    if match:
                        timestamp = datetime.strptime(
                            match.group(1), "%Y-%m-%d %H:%M:%S"
                        )
                        self.sessions.append(
                            SessionData(
                                timestamp=timestamp,
                                action=match.group(2),
                                session_type=match.group(3),
                                duration=int(match.group(4)),
                                date=timestamp.date(),
                            )
                        )
        except OSError:
            logger.exception("Error loading session data")

    def filter_sessions(self, period: str) -> List[SessionData]:
        """Filter sessions by time period"""
        now = datetime.now()

        if period == "day":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = now - timedelta(days=7)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        elif period == "year":
            cutoff = now - timedelta(days=365)
        else:  # all
            return self.sessions

        return [s for s in self.sessions if s.timestamp >= cutoff]

    def calculate_stats(self, sessions: List[SessionData]) -> Dict[str, Any]:
        """Calculate comprehensive productivity statistics"""
        completed_sessions = [s for s in sessions if s.action == "Completed"]
        work_sessions = [s for s in completed_sessions if s.session_type == "work"]
        break_sessions = [
            s
            for s in completed_sessions
            if s.session_type in ["short_break", "long_break"]
        ]

        total_work_time = sum(s.duration for s in work_sessions)
        total_break_time = sum(s.duration for s in break_sessions)

        # Get unique dates
        unique_dates = set(s.date for s in completed_sessions)

        stats = {
            "total_sessions": len(completed_sessions),
            "work_sessions": len(work_sessions),
            "break_sessions": len(break_sessions),
            "total_work_time": total_work_time,
            "total_break_time": total_break_time,
            "productive_hours": round(total_work_time / 60, 1),
            "days_active": len(unique_dates),
            "avg_work_session": (
                round(sum(s.duration for s in work_sessions) / len(work_sessions), 1)
                if work_sessions
                else 0
            ),
            "avg_break_session": (
                round(sum(s.duration for s in break_sessions) / len(break_sessions), 1)
                if break_sessions
                else 0
            ),
            "work_ratio": (
                round((len(work_sessions) / len(completed_sessions)) * 100, 1)
                if completed_sessions
                else 0
            ),
            "avg_sessions_per_day": (
                round(len(completed_sessions) / len(unique_dates), 1)
                if unique_dates
                else 0
            ),
            "avg_work_per_day": (
                round(total_work_time / len(unique_dates), 1) if unique_dates else 0
            ),
            "longest_work_session": max((s.duration for s in work_sessions), default=0),
            "shortest_work_session": min(
                (s.duration for s in work_sessions), default=0
            ),
            "total_focus_days": len(unique_dates),
            "streak_days": self._calculate_streak(sessions),
        }

        return stats

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick statistics summary for command line display"""
        # Get all sessions
        all_sessions = self.sessions
        total_stats = self.calculate_stats(all_sessions)

        # Get today's sessions
        today_sessions = self.filter_sessions("day")
        today_stats = self.calculate_stats(today_sessions)

        # Get week's sessions
        week_sessions = self.filter_sessions("week")
        week_stats = self.calculate_stats(week_sessions)

        # Calculate total minutes (work + break time)
        total_minutes = total_stats.get("total_work_time", 0) + total_stats.get(
            "total_break_time", 0
        )

        return {
            "today_sessions": today_stats.get("total_sessions", 0),
            "week_sessions": week_stats.get("total_sessions", 0),
            "total_sessions": total_stats.get("total_sessions", 0),
            "total_minutes": int(total_minutes),
            "streak": total_stats.get("streak_days", 0),
        }

    def _calculate_streak(self, sessions: List[SessionData]) -> int:
        """Calculate current streak of consecutive days with focus sessions"""
        if not sessions:
            return 0

        completed_sessions = [s for s in sessions if s.action == "Completed"]
        dates = sorted(set(s.date for s in completed_sessions), reverse=True)

        if not dates:
            return 0

        today = datetime.now().date()
        streak = 0

        # Check if today has sessions or yesterday (for streak continuity)
        if dates[0] == today or (
            len(dates) > 0 and dates[0] == today - timedelta(days=1)
        ):
            streak = 1
            last_date = dates[0]

            for date in dates[1:]:
                if last_date - date == timedelta(days=1):
                    streak += 1
                    last_date = date
                else:
                    break

        return streak

    def get_daily_breakdown(self, sessions: List[SessionData]) -> pd.DataFrame:
        """Generate daily breakdown statistics"""
        completed_sessions = [s for s in sessions if s.action == "Completed"]

        # Group by date
        daily_data = {}
        for session in completed_sessions:
            date_str = session.date.strftime("%Y-%m-%d")
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": session.date,
                    "total_sessions": 0,
                    "work_sessions": 0,
                    "work_minutes": 0,
                    "break_minutes": 0,
                }

            daily_data[date_str]["total_sessions"] += 1
            if session.session_type == "work":
                daily_data[date_str]["work_sessions"] += 1
                daily_data[date_str]["work_minutes"] += session.duration
            else:
                daily_data[date_str]["break_minutes"] += session.duration

        # Convert to DataFrame
        df_data = []
        for data in daily_data.values():
            df_data.append(
                {
                    "Date": data["date"],
                    "Sessions": data["total_sessions"],
                    "Work Sessions": data["work_sessions"],
                    "Work Minutes": data["work_minutes"],
                    "Work Hours": round(data["work_minutes"] / 60, 1),
                    "Break Minutes": data["break_minutes"],
                }
            )

        df = pd.DataFrame(df_data)
        if not df.empty:
            df = df.sort_values("Date", ascending=False)

        return df

    def get_hourly_pattern(self, sessions: List[SessionData]) -> Dict[int, int]:
        """Analyze productivity patterns by hour of day"""
        work_sessions = [
            s for s in sessions if s.action == "Completed" and s.session_type == "work"
        ]
        hourly_data = {}

        for hour in range(24):
            hourly_data[hour] = 0

        for session in work_sessions:
            hour = session.timestamp.hour
            hourly_data[hour] += session.duration

        return hourly_data

    def export_data(
        self, sessions: List[SessionData], stats: Dict[str, Any], daily_df: pd.DataFrame
    ) -> str:
        """Export data to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = EXPORTS_DIR
        export_dir.mkdir(parents=True, exist_ok=True)

        # Export raw sessions
        sessions_file = export_dir / f"focus_sessions_{timestamp}.csv"
        with open(sessions_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Action", "Type", "Duration", "Date"])
            for session in sessions:
                writer.writerow(
                    [
                        session.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        session.action,
                        session.session_type,
                        session.duration,
                        session.date.strftime("%Y-%m-%d"),
                    ]
                )

        # Export daily breakdown
        daily_file = export_dir / f"daily_breakdown_{timestamp}.csv"
        daily_df.to_csv(daily_file, index=False)

        # Export summary stats
        stats_file = export_dir / f"summary_stats_{timestamp}.json"
        with open(stats_file, "w", encoding="utf-8") as file:
            json.dump(stats, file, indent=2, default=str)

        return str(export_dir)


class DashboardGUI:
    """Advanced GUI dashboard with visualizations"""

    def __init__(self, analyzer: SessionAnalyzer):
        try:
            logger.debug("Initializing dashboard")
            self.analyzer = analyzer
            self.is_running = True
            self.check_running_id = None  # Track the scheduled callback

            logger.debug("Creating root window")
            self.root = tk.Tk()
            self.root.title("🎯 Focus Productivity Dashboard")
            self.root.geometry("1200x800")
            self.root.configure(bg="#2c3e50")

            # Set up proper window closing protocol
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Set up signal handlers for clean shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Configure style
            logger.debug("Configuring styles")
            self.style = ttk.Style()
            self.style.theme_use("clam")
            self.configure_styles()

            self.current_period = "week"
            logger.debug("Creating widgets")
            self.create_widgets()
            logger.debug("Updating dashboard")
            self.update_dashboard()
            logger.debug("Dashboard initialization complete")
        except Exception:
            logger.exception("Error during dashboard initialization")
            self.cleanup()
            raise

    def configure_styles(self):
        """Configure custom styles for the GUI"""
        # Configure notebook style
        self.style.configure("TNotebook", background="#2c3e50")
        self.style.configure(
            "TNotebook.Tab", background="#34495e", foreground="white", padding=[20, 10]
        )
        self.style.map("TNotebook.Tab", background=[("selected", "#3498db")])

        # Configure frame style
        self.style.configure(
            "Card.TFrame", background="#34495e", relief="raised", borderwidth=2
        )

    def signal_handler(self, signum, frame):
        """Handle system signals for clean shutdown"""
        logger.info("Received signal %s, shutting down dashboard", signum)
        self.cleanup()
        sys.exit(0)

    def on_closing(self):
        """Handle window close event"""
        logger.debug("Dashboard window closing")
        self.cleanup()

    def cleanup(self):
        """Clean up resources and close the application"""
        try:
            self.is_running = False

            # Cancel any scheduled callbacks
            if hasattr(self, "check_running_id") and self.check_running_id:
                try:
                    self.root.after_cancel(self.check_running_id)
                    self.check_running_id = None
                except Exception:
                    pass  # Ignore errors if already cancelled or invalid

            if hasattr(self, "root") and self.root:
                logger.debug("Destroying tkinter root window")
                try:
                    self.root.quit()  # Exit the mainloop
                except Exception:
                    pass  # Ignore errors if already destroyed
                try:
                    self.root.destroy()  # Destroy the window
                except Exception:
                    pass  # Ignore errors if already destroyed

            # Close any matplotlib figures
            plt.close("all")

            logger.debug("Dashboard cleanup complete")
        except Exception:
            logger.exception("Error during cleanup")
        finally:
            # Force exit if still running
            if hasattr(self, "is_running") and self.is_running:
                os._exit(0)

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🎯 FOCUS PRODUCTIVITY DASHBOARD",
            font=("Arial", 24, "bold"),
            fg="#ecf0f1",
            bg="#2c3e50",
        )
        title_label.pack(pady=20)

        # Control frame
        control_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        control_frame.pack(fill="x", padx=10)
        control_frame.pack_propagate(False)

        # Period selection
        tk.Label(
            control_frame, text="Period:", font=("Arial", 12), fg="white", bg="#2c3e50"
        ).pack(side="left", padx=(0, 10))

        self.period_var = tk.StringVar(value=self.current_period)
        period_combo = ttk.Combobox(
            control_frame,
            textvariable=self.period_var,
            values=["day", "week", "month", "year", "all"],
            state="readonly",
            width=10,
        )
        period_combo.pack(side="left", padx=(0, 20))
        period_combo.bind("<<ComboboxSelected>>", self.on_period_change)

        # Buttons
        ttk.Button(
            control_frame, text="🔄 Refresh", command=self.update_dashboard
        ).pack(side="left", padx=(0, 10))
        ttk.Button(control_frame, text="📊 Export Data", command=self.export_data).pack(
            side="left", padx=(0, 10)
        )
        ttk.Button(
            control_frame,
            text="📈 Generate Report",
            command=self.generate_visual_report,
        ).pack(side="left")

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Overview tab
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📊 Overview")

        # Charts tab
        self.charts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.charts_frame, text="📈 Charts")

        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text="📋 Details")

        self.create_overview_tab()
        self.create_charts_tab()
        self.create_details_tab()

    def create_overview_tab(self):
        """Create the overview statistics tab"""
        # Stats cards frame
        stats_frame = tk.Frame(self.overview_frame, bg="#2c3e50")
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create stats card containers
        self.stats_cards = {}

        # Top row - main stats
        top_frame = tk.Frame(stats_frame, bg="#2c3e50")
        top_frame.pack(fill="x", pady=(0, 10))

        for i, (key, title, color) in enumerate(
            [
                ("total_sessions", "Total Sessions", "#3498db"),
                ("work_sessions", "Work Sessions", "#2ecc71"),
                ("productive_hours", "Productive Hours", "#e74c3c"),
                ("days_active", "Active Days", "#f39c12"),
            ]
        ):
            card = self.create_stat_card(top_frame, title, "0", color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.stats_cards[key] = card

        # Middle row - averages
        mid_frame = tk.Frame(stats_frame, bg="#2c3e50")
        mid_frame.pack(fill="x", pady=(0, 10))

        for i, (key, title, color) in enumerate(
            [
                ("avg_work_session", "Avg Work Session", "#9b59b6"),
                ("avg_break_session", "Avg Break Session", "#1abc9c"),
                ("work_ratio", "Work Ratio %", "#34495e"),
                ("streak_days", "Current Streak", "#e67e22"),
            ]
        ):
            card = self.create_stat_card(mid_frame, title, "0", color)
            card.pack(side="left", fill="both", expand=True, padx=5)
            self.stats_cards[key] = card

        # Insights section
        insights_frame = ttk.LabelFrame(
            stats_frame, text="💡 Productivity Insights", style="Card.TFrame"
        )
        insights_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.insights_text = tk.Text(
            insights_frame,
            height=8,
            bg="#34495e",
            fg="white",
            font=("Consolas", 11),
            wrap="word",
            padx=10,
            pady=10,
        )
        self.insights_text.pack(fill="both", expand=True, padx=10, pady=10)

    def create_stat_card(self, parent, title, value, color):
        """Create a statistics card widget"""
        card = tk.Frame(parent, bg=color, relief="raised", bd=2)

        title_label = tk.Label(
            card, text=title, font=("Arial", 10, "bold"), fg="white", bg=color
        )
        title_label.pack(pady=(10, 5))

        value_label = tk.Label(
            card, text=value, font=("Arial", 24, "bold"), fg="white", bg=color
        )
        value_label.pack(pady=(0, 10))

        # Store reference to value label for updates
        card.value_label = value_label

        return card

    def create_charts_tab(self):
        """Create the charts and visualizations tab"""
        # Charts will be created dynamically
        self.charts_container = tk.Frame(self.charts_frame, bg="#2c3e50")
        self.charts_container.pack(fill="both", expand=True)

    def create_details_tab(self):
        """Create the detailed data tab"""
        # Treeview for daily breakdown
        columns = ("Date", "Sessions", "Work Sessions", "Work Hours", "Break Minutes")
        self.tree = ttk.Treeview(
            self.details_frame, columns=columns, show="headings", height=15
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.details_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def update_dashboard(self):
        """Update all dashboard data and visualizations"""
        # Get filtered data
        sessions = self.analyzer.filter_sessions(self.current_period)
        stats = self.analyzer.calculate_stats(sessions)
        daily_df = self.analyzer.get_daily_breakdown(sessions)

        # Update stats cards
        self.update_stats_cards(stats)

        # Update insights
        self.update_insights(stats, sessions)

        # Update charts
        self.update_charts(sessions, stats)

        # Update details table
        self.update_details_table(daily_df)

    def update_stats_cards(self, stats: Dict[str, Any]):
        """Update the statistics cards with current data"""
        card_mappings = {
            "total_sessions": str(stats["total_sessions"]),
            "work_sessions": str(stats["work_sessions"]),
            "productive_hours": f"{stats['productive_hours']}h",
            "days_active": str(stats["days_active"]),
            "avg_work_session": f"{stats['avg_work_session']}m",
            "avg_break_session": f"{stats['avg_break_session']}m",
            "work_ratio": f"{stats['work_ratio']}%",
            "streak_days": f"{stats['streak_days']} days",
        }

        for key, value in card_mappings.items():
            if key in self.stats_cards:
                self.stats_cards[key].value_label.config(text=value)

    def update_insights(self, stats: Dict[str, Any], sessions: List[SessionData]):
        """Generate and display productivity insights"""
        insights = []

        # Clear existing insights
        self.insights_text.delete(1.0, tk.END)

        # Generate insights based on data
        if stats["total_sessions"] == 0:
            insights.append(
                "🚀 Ready to start your productivity journey? Your first session awaits!"
            )
        else:
            # Productivity level insights
            if stats["productive_hours"] < 2:
                insights.append(
                    "🌱 Building momentum! Try to reach 2+ hours of focus time daily."
                )
            elif stats["productive_hours"] < 4:
                insights.append(
                    "📈 Good progress! You're developing a solid focus habit."
                )
            elif stats["productive_hours"] < 8:
                insights.append("🔥 Excellent focus! You're in the productivity zone!")
            else:
                insights.append("🏆 Outstanding! You're a productivity champion!")

            # Session length insights
            if stats["avg_work_session"] > 0:
                if stats["avg_work_session"] < 20:
                    insights.append(
                        "⏰ Consider longer work sessions (25-45 min) for deeper focus."
                    )
                elif stats["avg_work_session"] > 50:
                    insights.append(
                        "🛑 Great endurance! Consider adding more breaks to stay fresh."
                    )
                else:
                    insights.append(
                        "✅ Perfect session length for optimal focus and retention!"
                    )

            # Streak insights
            if stats["streak_days"] >= 7:
                insights.append(
                    f"🔥 Amazing {stats['streak_days']}-day streak! Consistency is key!"
                )
            elif stats["streak_days"] >= 3:
                insights.append(
                    f"💪 Great {stats['streak_days']}-day streak! Keep the momentum going!"
                )
            elif stats["streak_days"] == 0:
                insights.append(
                    "⭐ Start a new streak today! Consistency builds lasting habits."
                )

            # Work ratio insights
            if stats["work_ratio"] > 80:
                insights.append(
                    "🎯 High focus ratio! Remember to take breaks for optimal performance."
                )
            elif stats["work_ratio"] < 60:
                insights.append(
                    "🔄 Consider more work sessions relative to breaks for better flow."
                )

            # Daily average insights
            if stats["avg_sessions_per_day"] < 3:
                insights.append(
                    "📅 Try to aim for 3-5 sessions per day for better habit formation."
                )
            elif stats["avg_sessions_per_day"] > 8:
                insights.append(
                    "⚡ High session frequency! Ensure you're not burning out."
                )

        # Display insights
        for i, insight in enumerate(insights, 1):
            self.insights_text.insert(tk.END, f"{i}. {insight}\n\n")

        self.insights_text.config(state="disabled")

    def update_charts(self, sessions: List[SessionData], stats: Dict[str, Any]):
        """Update charts and visualizations"""
        # Clear existing charts
        for widget in self.charts_container.winfo_children():
            widget.destroy()

        if not sessions:
            no_data_label = tk.Label(
                self.charts_container,
                text="No data available for the selected period",
                font=("Arial", 16),
                fg="gray",
                bg="#2c3e50",
            )
            no_data_label.pack(expand=True)
            return

        # Create matplotlib figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.patch.set_facecolor("#2c3e50")

        # Daily productivity trend
        daily_df = self.analyzer.get_daily_breakdown(sessions)
        if not daily_df.empty:
            ax1.plot(
                daily_df["Date"],
                daily_df["Work Hours"],
                marker="o",
                color="#2ecc71",
                linewidth=2,
            )
            ax1.set_title(
                "Daily Productivity Trend",
                color="white",
                fontsize=12,
                fontweight="bold",
            )
            ax1.set_ylabel("Work Hours", color="white")
            ax1.tick_params(colors="white")
            ax1.grid(True, alpha=0.3)
            ax1.set_facecolor("#34495e")

        # Session type distribution
        session_types = {}
        for session in sessions:
            if session.action == "Completed":
                session_types[session.session_type] = (
                    session_types.get(session.session_type, 0) + 1
                )

        if session_types:
            labels = list(session_types.keys())
            values = list(session_types.values())
            colors = ["#2ecc71", "#3498db", "#e74c3c"][: len(labels)]
            ax2.pie(
                values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90
            )
            ax2.set_title(
                "Session Type Distribution",
                color="white",
                fontsize=12,
                fontweight="bold",
            )

        # Hourly productivity pattern
        hourly_data = self.analyzer.get_hourly_pattern(sessions)
        hours = list(hourly_data.keys())
        minutes = list(hourly_data.values())

        ax3.bar(hours, minutes, color="#9b59b6", alpha=0.7)
        ax3.set_title(
            "Productivity by Hour", color="white", fontsize=12, fontweight="bold"
        )
        ax3.set_xlabel("Hour of Day", color="white")
        ax3.set_ylabel("Work Minutes", color="white")
        ax3.tick_params(colors="white")
        ax3.set_facecolor("#34495e")

        # Weekly focus trend (last 7 days)
        recent_sessions = [
            s for s in sessions if s.timestamp >= datetime.now() - timedelta(days=7)
        ]
        weekly_data = {}
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).date()
            weekly_data[date.strftime("%a")] = 0

        for session in recent_sessions:
            if session.action == "Completed" and session.session_type == "work":
                day_name = session.timestamp.strftime("%a")
                if day_name in weekly_data:
                    weekly_data[day_name] += session.duration

        days = list(weekly_data.keys())
        minutes = list(weekly_data.values())

        ax4.bar(days, minutes, color="#e67e22", alpha=0.7)
        ax4.set_title(
            "Weekly Focus Pattern", color="white", fontsize=12, fontweight="bold"
        )
        ax4.set_ylabel("Work Minutes", color="white")
        ax4.tick_params(colors="white")
        ax4.set_facecolor("#34495e")

        # Style all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.spines["bottom"].set_color("white")
            ax.spines["top"].set_color("white")
            ax.spines["right"].set_color("white")
            ax.spines["left"].set_color("white")

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.charts_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_details_table(self, daily_df: pd.DataFrame):
        """Update the details table with daily breakdown"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for _, row in daily_df.iterrows():
            self.tree.insert(
                "",
                "end",
                values=(
                    row["Date"].strftime("%Y-%m-%d"),
                    row["Sessions"],
                    row["Work Sessions"],
                    row["Work Hours"],
                    row["Break Minutes"],
                ),
            )

    def on_period_change(self, event=None):
        """Handle period selection change"""
        self.current_period = self.period_var.get()
        self.update_dashboard()

    def export_data(self):
        """Export dashboard data"""
        try:
            sessions = self.analyzer.filter_sessions(self.current_period)
            stats = self.analyzer.calculate_stats(sessions)
            daily_df = self.analyzer.get_daily_breakdown(sessions)

            export_path = self.analyzer.export_data(sessions, stats, daily_df)
            messagebox.showinfo("Export Complete", f"Data exported to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{str(e)}")

    def generate_visual_report(self):
        """Generate a comprehensive visual report"""
        try:
            # Ask user for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")],
                title="Save Report As",
            )

            if filename:
                sessions = self.analyzer.filter_sessions(self.current_period)
                if not sessions:
                    messagebox.showinfo(
                        "No Data",
                        "No sessions available for the selected period to generate a report.",
                    )
                    return

                # Create a comprehensive report figure
                fig, axes = plt.subplots(3, 2, figsize=(15, 12))
                fig.patch.set_facecolor("white")
                fig.suptitle(
                    f"Focus Productivity Report — {self.current_period.title()} View",
                    fontsize=16,
                    fontweight="bold",
                    color="#2c3e50",
                )

                # ── Chart 1: Daily productivity trend ─────────────────────────
                ax1 = axes[0, 0]
                daily_df = self.analyzer.get_daily_breakdown(sessions)
                if not daily_df.empty:
                    ax1.plot(
                        daily_df["Date"],
                        daily_df["Work Hours"],
                        marker="o",
                        color="#2ecc71",
                        linewidth=2,
                    )
                    ax1.fill_between(
                        daily_df["Date"],
                        daily_df["Work Hours"],
                        alpha=0.15,
                        color="#2ecc71",
                    )
                ax1.set_title(
                    "Daily Productivity Trend", fontsize=12, fontweight="bold"
                )
                ax1.set_ylabel("Work Hours")
                ax1.grid(True, alpha=0.3)

                # ── Chart 2: Session type pie ──────────────────────────────────
                ax2 = axes[0, 1]
                session_types_cnt: dict = {}
                for s in sessions:
                    if s.action == "Completed":
                        session_types_cnt[s.session_type] = (
                            session_types_cnt.get(s.session_type, 0) + 1
                        )
                if session_types_cnt:
                    pie_labels = list(session_types_cnt.keys())
                    pie_values = list(session_types_cnt.values())
                    pie_colors = ["#2ecc71", "#3498db", "#e74c3c"][: len(pie_labels)]
                    ax2.pie(
                        pie_values,
                        labels=pie_labels,
                        colors=pie_colors,
                        autopct="%1.1f%%",
                        startangle=90,
                    )
                ax2.set_title(
                    "Session Type Distribution", fontsize=12, fontweight="bold"
                )

                # ── Chart 3: Hourly productivity pattern ──────────────────────
                ax3 = axes[1, 0]
                hourly_data = self.analyzer.get_hourly_pattern(sessions)
                ax3.bar(
                    list(hourly_data.keys()),
                    list(hourly_data.values()),
                    color="#9b59b6",
                    alpha=0.7,
                )
                ax3.set_title("Productivity by Hour", fontsize=12, fontweight="bold")
                ax3.set_xlabel("Hour of Day")
                ax3.set_ylabel("Work Minutes")
                ax3.grid(True, alpha=0.3)

                # ── Chart 4: Weekly focus pattern ──────────────────────────────
                ax4 = axes[1, 1]
                recent = [
                    s
                    for s in sessions
                    if s.timestamp >= datetime.now() - timedelta(days=7)
                ]
                weekly: dict = {}
                for i in range(7):
                    weekly[(datetime.now() - timedelta(days=i)).strftime("%a")] = 0
                for s in recent:
                    if s.action == "Completed" and s.session_type == "work":
                        dn = s.timestamp.strftime("%a")
                        if dn in weekly:
                            weekly[dn] += s.duration
                ax4.bar(
                    list(weekly.keys()),
                    list(weekly.values()),
                    color="#e67e22",
                    alpha=0.7,
                )
                ax4.set_title(
                    "Weekly Focus Pattern (Last 7 Days)", fontsize=12, fontweight="bold"
                )
                ax4.set_ylabel("Work Minutes")
                ax4.grid(True, alpha=0.3)

                # ── Panel 5: Key statistics ────────────────────────────────────
                ax5 = axes[2, 0]
                ax5.axis("off")
                stats = self.analyzer.calculate_stats(sessions)
                stats_text = (
                    "KEY STATISTICS\n\n"
                    f"  Total Sessions:    {stats['total_sessions']}\n"
                    f"  Work Sessions:     {stats['work_sessions']}\n"
                    f"  Productive Hours:  {stats['productive_hours']} h\n"
                    f"  Days Active:       {stats['days_active']}\n"
                    f"  Avg Work Session:  {stats['avg_work_session']} min\n"
                    f"  Avg Break Session: {stats['avg_break_session']} min\n"
                    f"  Work Ratio:        {stats['work_ratio']} %\n"
                    f"  Current Streak:    {stats['streak_days']} days"
                )
                ax5.text(
                    0.05,
                    0.95,
                    stats_text,
                    transform=ax5.transAxes,
                    fontsize=11,
                    verticalalignment="top",
                    fontfamily="monospace",
                    color="#2c3e50",
                )

                # ── Panel 6: Insights ──────────────────────────────────────────
                ax6 = axes[2, 1]
                ax6.axis("off")
                if stats["productive_hours"] >= 8:
                    insight = "Outstanding! You are a productivity champion."
                elif stats["productive_hours"] >= 4:
                    insight = "Excellent focus! You are in the productivity zone."
                elif stats["productive_hours"] >= 2:
                    insight = "Good progress! Keep building your focus habit."
                else:
                    insight = "Building momentum — aim for 2+ hours daily."
                streak_note = (
                    f"  {stats['streak_days']}-day active streak!"
                    if stats["streak_days"] >= 3
                    else "  Start a streak — consistency builds habits."
                )
                ax6.text(
                    0.05,
                    0.95,
                    f"INSIGHTS\n\n  {insight}\n\n{streak_note}",
                    transform=ax6.transAxes,
                    fontsize=11,
                    verticalalignment="top",
                    fontfamily="monospace",
                    color="#2c3e50",
                )

                plt.tight_layout()
                plt.savefig(filename, dpi=300, bbox_inches="tight", facecolor="white")
                plt.close()

                messagebox.showinfo(
                    "Report Generated", f"Visual report saved to:\n{filename}"
                )
        except Exception as e:
            messagebox.showerror(
                "Report Error", f"Failed to generate report:\n{str(e)}"
            )

    def run(self):
        """Start the dashboard GUI"""
        try:
            logger.debug("Starting dashboard GUI mainloop")
            # Make the window interruptible by checking periodically
            self.check_running_id = self.root.after(100, self.check_running)
            self.root.mainloop()
            logger.debug("Dashboard GUI mainloop ended")
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.cleanup()
        except Exception:
            logger.exception("Error in dashboard mainloop")
            self.cleanup()
        finally:
            logger.debug("Dashboard run method completed")
            self.cleanup()

    def check_running(self):
        """Periodically check if the application should continue running"""
        if self.is_running and self.root and self.root.winfo_exists():
            self.check_running_id = self.root.after(100, self.check_running)
        else:
            self.cleanup()


class LauncherGUI:
    """GUI launcher for selecting application mode"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Focus Timer Launcher")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")

        # Center window
        self.center_window()

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
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
        self.style.configure(
            "Title.TLabel",
            font=("Arial", 20, "bold"),
            background="#2c3e50",
            foreground="#ecf0f1",
        )

        self.style.configure(
            "Subtitle.TLabel",
            font=("Arial", 10),
            background="#2c3e50",
            foreground="#bdc3c7",
        )

        self.style.configure(
            "Launch.TButton", font=("Arial", 12, "bold"), padding=(16, 12)
        )

        self.style.configure("Option.TButton", font=("Arial", 10), padding=(12, 8))

        self.style.configure(
            "Card.TFrame",
            background="#34495e",
            relief="raised",
            borderwidth=2,
        )

    def create_widgets(self):
        """Create and layout widgets"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=120)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(
            header_frame, text="🎯 FOCUS TIMER", style="Title.TLabel"
        )
        title_label.pack(pady=(20, 5))

        subtitle_label = ttk.Label(
            header_frame,
            text="Boost your productivity with the Pomodoro Technique",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack()

        # Main content
        content_frame = tk.Frame(self.root, bg="#2c3e50")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Launch options
        options_frame = ttk.Frame(content_frame, style="Card.TFrame")
        options_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Option 1: GUI Timer
        gui_frame = tk.Frame(options_frame, bg="#34495e")
        gui_frame.pack(fill="x", padx=20, pady=(20, 10))

        gui_icon = tk.Label(
            gui_frame, text="🖥️", font=("Arial", 28), bg="#34495e", fg="#3498db"
        )
        gui_icon.pack(side="left", padx=(0, 15))

        gui_info = tk.Frame(gui_frame, bg="#34495e")
        gui_info.pack(side="left", fill="both", expand=True)

        gui_title = tk.Label(
            gui_info,
            text="GUI Timer",
            font=("Arial", 14, "bold"),
            bg="#34495e",
            fg="white",
        )
        gui_title.pack(anchor="w")

        gui_desc = tk.Label(
            gui_info,
            text="Modern graphical interface with progress bars,\nstatistics, and easy session management",
            font=("Arial", 9),
            bg="#34495e",
            fg="#bdc3c7",
        )
        gui_desc.pack(anchor="w")

        gui_button = ttk.Button(
            gui_frame,
            text="Launch GUI",
            style="Launch.TButton",
            command=self.launch_gui,
        )
        gui_button.pack(side="right", padx=(10, 0))

        # Separator
        separator1 = ttk.Separator(options_frame, orient="horizontal")
        separator1.pack(fill="x", padx=20, pady=10)

        # Option 2: Console Timer
        console_frame = tk.Frame(options_frame, bg="#34495e")
        console_frame.pack(fill="x", padx=20, pady=10)

        console_icon = tk.Label(
            console_frame, text="⌨️", font=("Arial", 28), bg="#34495e", fg="#2ecc71"
        )
        console_icon.pack(side="left", padx=(0, 15))

        console_info = tk.Frame(console_frame, bg="#34495e")
        console_info.pack(side="left", fill="both", expand=True)

        console_title = tk.Label(
            console_info,
            text="Console Timer",
            font=("Arial", 14, "bold"),
            bg="#34495e",
            fg="white",
        )
        console_title.pack(anchor="w")

        console_desc = tk.Label(
            console_info,
            text="Terminal-based interface for keyboard enthusiasts\nand minimal resource usage",
            font=("Arial", 9),
            bg="#34495e",
            fg="#bdc3c7",
        )
        console_desc.pack(anchor="w")

        console_button = ttk.Button(
            console_frame,
            text="Launch Console",
            style="Launch.TButton",
            command=self.launch_console,
        )
        console_button.pack(side="right", padx=(10, 0))

        # Separator
        separator2 = ttk.Separator(options_frame, orient="horizontal")
        separator2.pack(fill="x", padx=20, pady=10)

        # Option 3: Analytics Dashboard
        dashboard_frame = tk.Frame(options_frame, bg="#34495e")
        dashboard_frame.pack(fill="x", padx=20, pady=10)

        dashboard_icon = tk.Label(
            dashboard_frame, text="📊", font=("Arial", 28), bg="#34495e", fg="#e74c3c"
        )
        dashboard_icon.pack(side="left", padx=(0, 15))

        dashboard_info = tk.Frame(dashboard_frame, bg="#34495e")
        dashboard_info.pack(side="left", fill="both", expand=True)

        dashboard_title = tk.Label(
            dashboard_info,
            text="Analytics Dashboard",
            font=("Arial", 14, "bold"),
            bg="#34495e",
            fg="white",
        )
        dashboard_title.pack(anchor="w")

        dashboard_desc = tk.Label(
            dashboard_info,
            text="Detailed productivity analytics with charts,\ninsights, and session history",
            font=("Arial", 9),
            bg="#34495e",
            fg="#bdc3c7",
        )
        dashboard_desc.pack(anchor="w")

        dashboard_button = ttk.Button(
            dashboard_frame,
            text="View Analytics",
            style="Launch.TButton",
            command=self.launch_dashboard,
        )
        dashboard_button.pack(side="right", padx=(10, 0))

        # Bottom section
        bottom_frame = tk.Frame(content_frame, bg="#2c3e50")
        bottom_frame.pack(fill="x", pady=(20, 0))

        # Utility buttons
        utils_frame = tk.Frame(bottom_frame, bg="#2c3e50")
        utils_frame.pack(fill="x")

        ttk.Button(
            utils_frame,
            text="⚙️ Configuration",
            style="Option.TButton",
            command=self.open_config,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            utils_frame,
            text="📁 Open Data Folder",
            style="Option.TButton",
            command=self.open_data_folder,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            utils_frame, text="🆘 Help", style="Option.TButton", command=self.show_help
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            utils_frame, text="❌ Exit", style="Option.TButton", command=self.root.quit
        ).pack(side="right")

        # Status bar
        status_frame = tk.Frame(bottom_frame, bg="#2c3e50", height=30)
        status_frame.pack(fill="x", pady=(10, 0))
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            status_frame,
            text="Ready to focus! Select an option above to begin.",
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#95a5a6",
        )
        self.status_label.pack(side="left", pady=5)

        version_label = tk.Label(
            status_frame,
            text="v2.0 Python Edition",
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#95a5a6",
        )
        version_label.pack(side="right", pady=5)

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
            gui = FocusGUI()
            gui.run()

            # Show launcher again when GUI closes
            self.root.deiconify()
            self.update_status("GUI Timer closed. Ready for next session!")

        except Exception as e:
            messagebox.showerror(
                "Launch Error", f"Failed to launch GUI Timer:\n{str(e)}"
            )
            self.update_status("Error launching GUI Timer")

    def launch_console(self):
        """Launch the console timer"""
        try:
            self.update_status("Launching Console Timer...")

            # Launch in new terminal/command prompt
            python_exe = sys.executable
            script_path = Path(__file__).parent / "src" / "focus_console.py"

            if os.name == "nt":  # Windows
                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "cmd",
                        "/k",
                        f'"{python_exe}" "{script_path}" --interactive',
                    ]
                )
            elif os.name == "posix":  # macOS/Linux
                if sys.platform == "darwin":  # macOS
                    subprocess.Popen(
                        [
                            "osascript",
                            "-e",
                            f'tell application "Terminal" to do script "{python_exe} {script_path} --interactive"',
                        ]
                    )
                else:  # Linux
                    # Try different terminal emulators
                    terminals = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]
                    for terminal in terminals:
                        try:
                            subprocess.Popen(
                                [
                                    terminal,
                                    "-e",
                                    f"{python_exe} {script_path} --interactive",
                                ]
                            )
                            break
                        except FileNotFoundError:
                            continue
                    else:
                        # Fallback: run in current terminal
                        subprocess.Popen(
                            [python_exe, str(script_path), "--interactive"]
                        )

            self.update_status("Console Timer launched in new terminal")

        except Exception as e:
            messagebox.showerror(
                "Launch Error", f"Failed to launch Console Timer:\n{str(e)}"
            )
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
            messagebox.showerror(
                "Launch Error", f"Failed to launch Analytics Dashboard:\n{str(e)}"
            )
            self.update_status("Error launching Analytics Dashboard")

    def open_config(self):
        """Open configuration file"""
        try:
            config = ConfigManager()
            config_path = config.config_path

            if config_path.exists():
                if os.name == "nt":  # Windows
                    os.startfile(str(config_path))
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(config_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(config_path)])

                self.update_status(f"Opened configuration file: {config_path}")
            else:
                messagebox.showwarning(
                    "File Not Found", "Configuration file not found!"
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open configuration:\n{str(e)}")

    def open_data_folder(self):
        """Open the data folder"""
        try:
            config = ConfigManager()
            data_path = config.get_app_config()["data_path"]
            data_dir = Path(data_path).parent

            if data_dir.exists():
                if os.name == "nt":  # Windows
                    os.startfile(str(data_dir))
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(data_dir)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(data_dir)])

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
        help_window.configure(bg="#2c3e50")

        # Text widget with scrollbar
        text_frame = tk.Frame(help_window, bg="#2c3e50")
        text_frame.pack(fill="both", expand=True, padx=20, pady=20)

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            bg="#34495e",
            fg="white",
            font=("Consolas", 11),
            padx=15,
            pady=15,
        )
        scrollbar = ttk.Scrollbar(
            text_frame, orient="vertical", command=text_widget.yview
        )
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")

        # Close button
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=10)

    def run(self):
        """Start the launcher GUI"""
        self.root.mainloop()


class CustomSessionDialog:
    """Dialog for creating custom duration sessions"""

    def __init__(self, parent):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Custom Session")
        self.dialog.geometry("300x200")
        self.dialog.resizable(True, True)

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

    def __init__(
        self,
        parent,
        config_manager,
        google_integration=None,
        task_manager: Optional[TaskManager] = None,
    ):
        self.config = config_manager
        self.google_integration = google_integration
        self.task_manager = task_manager
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)

        self.dialog.transient(parent)
        self.dialog.grab_set()

        default_credentials_path = (
            str(self.google_integration.credentials_file)
            if self.google_integration
            else str(Path.home() / ".ultimate-focus-timer" / "google_credentials.json")
        )
        self.google_credentials_path = tk.StringVar(
            master=self.dialog, value=default_credentials_path
        )
        self.google_status_var = tk.StringVar(master=self.dialog, value="")
        self.google_task_list_var = tk.StringVar(master=self.dialog, value="")
        self.google_task_list_lookup: Dict[str, str] = {}
        self.google_task_list_combo = None

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.create_timer_tab(notebook)
        self.create_music_tab(notebook)
        self.create_notifications_tab(notebook)
        self.create_tasks_tab(notebook)
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

    @staticmethod
    def _task_list_display(
        title: str, task_list_id: str, existing: Optional[Dict[str, str]] = None
    ) -> str:
        """Format a task list label for the settings combobox."""
        display = title.strip() or f"List {task_list_id}"
        if existing and display in existing and existing[display] != task_list_id:
            return f"{display} ({task_list_id})"
        return display

    def create_tasks_tab(self, notebook):
        """Create Google Tasks settings tab."""
        tab = ttk.Frame(notebook, padding="10")
        notebook.add(tab, text="Tasks")
        tab.grid_columnconfigure(1, weight=1)

        ttk.Label(tab, text="Google Tasks Status:").grid(
            row=0, column=0, sticky=tk.NW, pady=5
        )
        ttk.Label(
            tab,
            textvariable=self.google_status_var,
            wraplength=320,
            justify=tk.LEFT,
        ).grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(tab, text="OAuth Client JSON:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(tab, textvariable=self.google_credentials_path, width=40).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=5
        )
        ttk.Button(tab, text="Browse...", command=self.browse_google_credentials).grid(
            row=1, column=2, padx=(5, 0), pady=5, sticky=tk.W
        )
        ttk.Button(
            tab, text="Paste JSON...", command=self.paste_google_credentials
        ).grid(row=1, column=3, padx=(5, 0), pady=5, sticky=tk.W)

        actions = ttk.Frame(tab)
        actions.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(5, 10))
        ttk.Button(
            actions,
            text="Connect Google Tasks",
            command=self.connect_google_tasks,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            actions,
            text="Disconnect",
            command=self.disconnect_google_tasks,
        ).pack(side=tk.LEFT)

        ttk.Label(tab, text="Google Task List:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self.google_task_list_combo = ttk.Combobox(
            tab,
            textvariable=self.google_task_list_var,
            state="readonly",
            width=40,
        )
        self.google_task_list_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(
            tab, text="Refresh Lists", command=self.refresh_google_task_lists
        ).grid(row=3, column=2, padx=(5, 0), pady=5, sticky=tk.W)
        ttk.Button(
            tab, text="Enable Tasks API", command=self.open_google_tasks_api_setup
        ).grid(row=3, column=3, padx=(5, 0), pady=5, sticky=tk.W)

        ttk.Label(
            tab,
            text=(
                "Click Connect Google Tasks to launch setup if needed, then open "
                "your browser for Google sign-in. The saved token stays local on "
                "this machine."
            ),
            wraplength=420,
            justify=tk.LEFT,
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        self.refresh_google_status()
        self.refresh_google_task_lists()

    def browse_google_credentials(self, connect_after_install: bool = False):
        """Pick and install a Google OAuth client JSON file."""
        selected = filedialog.askopenfilename(
            parent=self.dialog,
            title="Select Google OAuth Client JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not selected:
            return False

        try:
            if self.google_integration:
                installed = self.google_integration.install_credentials_file(Path(selected))
                self.google_credentials_path.set(str(installed))
            else:
                self.google_credentials_path.set(selected)
            self.refresh_google_status()
            if connect_after_install:
                self.dialog.after(0, self.connect_google_tasks)
            return True
        except Exception as exc:
            messagebox.showerror(
                "Google Tasks",
                f"Failed to install Google OAuth JSON:\n{exc}",
            )
            return False

    def open_google_oauth_setup(self):
        """Open the Google Cloud page for creating a Desktop OAuth client."""
        self._open_external_url(
            GOOGLE_OAUTH_SETUP_URL,
            "Failed to open Google Cloud setup",
        )

    def open_google_tasks_api_setup(self):
        """Open the Google Cloud page for enabling the Google Tasks API."""
        help_url = GOOGLE_TASKS_API_OVERVIEW_URL
        if self.google_integration:
            status = self.google_integration.get_connection_status()
            help_url = status.get("last_error_help_url") or help_url
        self._open_external_url(
            help_url,
            "Failed to open Google Tasks API page",
        )

    @staticmethod
    def _open_external_url(url: str, error_prefix: str):
        """Open an external URL in the default browser."""
        try:
            opened = webbrowser.open(url, new=2)
            if not opened and hasattr(os, "startfile"):
                os.startfile(url)
                opened = True
            if not opened:
                raise RuntimeError("Could not launch the default browser.")
        except Exception as exc:
            messagebox.showerror(
                "Google Tasks",
                f"{error_prefix}:\n{exc}",
            )

    def _sync_google_tasks_after_connect(self):
        """Pull Google tasks in the background after a successful connection."""
        if not self.task_manager:
            return

        def _worker():
            try:
                summary = self.task_manager.sync_with_cloud()
                logger.info("Google task sync after connect: %s", summary)
            except Exception:
                logger.exception("Failed to sync tasks after Google connect")

        threading.Thread(target=_worker, daemon=True).start()

    def _browse_credentials_from_dialog(
        self, dialog: tk.Toplevel, connect_after_install: bool = False
    ):
        """Install a JSON file from a child dialog and optionally continue to OAuth."""
        if self.browse_google_credentials(connect_after_install=connect_after_install):
            dialog.destroy()

    def paste_google_credentials(self, connect_after_install: bool = False):
        """Paste the OAuth client JSON and optionally continue into browser auth."""
        paste_win = tk.Toplevel(self.dialog)
        paste_win.title("Paste Google OAuth JSON")
        paste_win.geometry("640x460")
        paste_win.transient(self.dialog)
        paste_win.grab_set()

        header = ttk.Frame(paste_win, padding="10")
        header.pack(fill=tk.X)
        ttk.Label(
            header,
            text=(
                "Google Tasks needs a one-time OAuth Desktop App JSON from Google Cloud. "
                "If you do not have one yet, click Open Google Cloud, create a Desktop "
                "app OAuth client, then paste the JSON below."
            ),
            wraplength=600,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        helper_actions = ttk.Frame(header)
        helper_actions.pack(anchor=tk.W, pady=(8, 0))
        ttk.Button(
            helper_actions,
            text="Open Google Cloud",
            command=self.open_google_oauth_setup,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            helper_actions,
            text="Browse JSON...",
            command=lambda: self._browse_credentials_from_dialog(
                paste_win, connect_after_install
            ),
        ).pack(side=tk.LEFT)

        text = tk.Text(paste_win, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        button_frame = ttk.Frame(paste_win)
        button_frame.pack(pady=8)

        def do_install(continue_to_connect: bool = False):
            content = text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Paste credentials", "No content provided.")
                return
            try:
                if self.google_integration:
                    target = self.google_integration.install_credentials_content(content)
                else:
                    target = Path(self.google_credentials_path.get()).expanduser()
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                self.google_credentials_path.set(str(target))
                self.refresh_google_status()
                messagebox.showinfo(
                    "Paste credentials", f"Credentials saved to {target}"
                )
                paste_win.destroy()
                if continue_to_connect or connect_after_install:
                    self.dialog.after(0, self.connect_google_tasks)
            except Exception as exc:
                messagebox.showerror(
                    "Paste credentials", f"Failed to save credentials: {exc}"
                )

        ttk.Button(
            button_frame, text="Install", command=lambda: do_install(False)
        ).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            button_frame,
            text="Install and Connect",
            command=lambda: do_install(True),
        ).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=paste_win.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def _current_google_task_list_id(self) -> str:
        """Return the selected Google task list id."""
        selected_display = self.google_task_list_var.get().strip()
        if selected_display in self.google_task_list_lookup:
            return self.google_task_list_lookup[selected_display]
        return self.config.get("google_task_list_id", DEFAULT_TASK_LIST_ID)

    def _sync_task_manager(self):
        """Apply the active Google integration settings to the task manager."""
        if self.task_manager:
            self.task_manager.set_google_integration(
                self.google_integration,
                self._current_google_task_list_id(),
            )

    def refresh_google_status(self):
        """Refresh the Google Tasks connection label."""
        if not self.google_integration:
            self.google_status_var.set("Google Tasks integration is unavailable.")
            return

        status = self.google_integration.get_connection_status()
        if not status["api_available"]:
            self.google_status_var.set(
                "Google API packages are not installed. Install the project "
                "requirements to enable Google Tasks."
            )
        elif status.get("last_error"):
            self.google_status_var.set(status["last_error"])
        elif status["connected"]:
            self.google_status_var.set("Connected. Google Tasks sync is ready.")
        elif status["has_credentials_file"]:
            self.google_status_var.set(
                "OAuth client file found. Click Connect Google Tasks to sign in "
                "in your browser."
            )
        else:
            self.google_status_var.set(
                "Not connected. Click Connect Google Tasks to start the one-time "
                "setup, save your OAuth JSON, and open the browser sign-in flow."
            )

    def refresh_google_task_lists(self):
        """Load task lists for the connected account and refresh the combobox."""
        saved_task_list_id = self.config.get(
            "google_task_list_id", DEFAULT_TASK_LIST_ID
        )
        options = {
            self._task_list_display(
                "Primary task list", DEFAULT_TASK_LIST_ID
            ): DEFAULT_TASK_LIST_ID
        }

        if self.google_integration and self.google_integration.is_enabled():
            for task_list in self.google_integration.get_task_lists():
                display = self._task_list_display(
                    task_list["title"], task_list["id"], options
                )
                options[display] = task_list["id"]
            self.refresh_google_status()
        elif saved_task_list_id != DEFAULT_TASK_LIST_ID:
            options[
                self._task_list_display("Saved task list", saved_task_list_id, options)
            ] = saved_task_list_id

        self.google_task_list_lookup = options
        values = list(options.keys())
        if self.google_task_list_combo:
            self.google_task_list_combo["values"] = values
            self.google_task_list_combo.config(
                state="readonly" if values else "disabled"
            )

        for display, task_list_id in options.items():
            if task_list_id == saved_task_list_id:
                self.google_task_list_var.set(display)
                break
        else:
            self.google_task_list_var.set(values[0])

    def connect_google_tasks(self):
        """Connect Google Tasks and launch browser-based OAuth."""
        if not self.google_integration:
            messagebox.showerror(
                "Google Tasks", "Google Tasks integration is unavailable."
            )
            return

        credentials_source = None
        raw_credentials_path = self.google_credentials_path.get().strip()
        if raw_credentials_path:
            candidate = Path(raw_credentials_path).expanduser()
            if candidate.exists():
                credentials_source = candidate

        if credentials_source is None and not self.google_integration.has_credentials_file():
            self.paste_google_credentials(connect_after_install=True)
            self.refresh_google_status()
            return

        try:
            connected = self.google_integration.connect(credentials_source)
        except FileNotFoundError as exc:
            messagebox.showwarning(
                "Google Tasks",
                f"{exc}\n\nPaste or browse your Google OAuth JSON to finish setup.",
            )
            self.refresh_google_status()
            return
        except RuntimeError as exc:
            messagebox.showerror("Google Tasks", str(exc))
            self.refresh_google_status()
            return
        except Exception as exc:
            messagebox.showerror(
                "Google Tasks",
                f"Failed to connect Google Tasks:\n{exc}",
            )
            self.refresh_google_status()
            return

        if not connected:
            messagebox.showerror(
                "Google Tasks",
                "Google Tasks could not be connected.",
            )
            self.refresh_google_status()
            return

        self.google_credentials_path.set(str(self.google_integration.credentials_file))
        self.refresh_google_status()
        self.refresh_google_task_lists()
        self._sync_task_manager()
        self._sync_google_tasks_after_connect()
        messagebox.showinfo(
            "Google Tasks",
            "Google Tasks connected. The app will keep the token locally and "
            "start syncing your tasks automatically.",
        )

    def disconnect_google_tasks(self):
        """Remove the saved Google token from this device."""
        if not self.google_integration:
            messagebox.showerror(
                "Google Tasks", "Google Tasks integration is unavailable."
            )
            return

        try:
            self.google_integration.disconnect()
        except Exception as exc:
            messagebox.showerror(
                "Google Tasks",
                f"Failed to disconnect Google Tasks:\n{exc}",
            )
            return

        self.refresh_google_status()
        self.refresh_google_task_lists()
        self._sync_task_manager()
        messagebox.showinfo(
            "Google Tasks",
            "Google Tasks disconnected on this device.",
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
            self.config.set("google_task_list_id", self._current_google_task_list_id())

            if self.config.save_config():
                self._sync_task_manager()
                if self.google_integration and self.google_integration.is_enabled():
                    self._sync_google_tasks_after_connect()
                messagebox.showinfo(
                    "Settings Saved",
                    "Settings saved successfully.",
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
        self.dialog.resizable(True, True)
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
            font=("Arial", 13, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Instruction
        instruction_label = ttk.Label(
            main_frame, text="Which task were you working on?", font=("Arial", 11)
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
                font=("Arial", 10, "italic"),
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


class FocusGUI:
    """Modern GUI for the Focus Timer application"""

    def __init__(self):
        """Initialize the GUI application"""
        try:
            # Initialize components
            self.config = ConfigManager()
            self.music = MusicController(self.config)
            self.notifications = NotificationManager(self.config)
            self.session_manager = SessionManager(self.config)

            # Initialize task manager
            self.google_config_dir = Path.home() / ".ultimate-focus-timer"
            self.google_integration = create_google_integration(self.google_config_dir)
            self.task_manager = TaskManager(
                google_integration=self.google_integration,
                google_task_list_id=self.config.get(
                    "google_task_list_id", DEFAULT_TASK_LIST_ID
                ),
            )

            # Add a variable to store the current task ID
            self.current_task_id = None

            # Store scheduled callback IDs for proper cleanup
            self.scheduled_callbacks = []

            # ── Daemon manager ─────────────────────────────────────────────────
            self.daemon_manager = DaemonManager(
                on_status_changed=self._on_daemon_status_changed
            )
            self.daemon_status_label = None  # Will be set in create_widgets
            self.daemon_start_button = None
            self.daemon_stop_button = None
            self.tray = TrayManager(
                on_show=self._show_window,
                on_start_work=lambda: self._marshal(
                    lambda: self.start_session(SessionType.WORK)
                ),
                on_start_break=lambda: self._marshal(
                    lambda: self.start_session(SessionType.SHORT_BREAK)
                ),
                on_pause_resume=lambda: self._marshal(self.toggle_pause),
                on_stop=lambda: self._marshal(self.stop_session),
                on_quit=lambda: self._marshal(self.on_closing),
            )
            self.tray.start()

            # ── Global hotkeys ─────────────────────────────────────────────────
            self.hotkeys = HotkeyManager(
                on_show=self._show_window,
                on_pause_resume=lambda: self._marshal(self.toggle_pause),
            )
            self.hotkeys.start()

            # Wire all session events — GUI handles music + notifications directly
            self.session_manager.set_callbacks(
                on_tick=self.on_session_tick,
                on_complete=self.on_session_complete,
                on_state_change=self.on_session_state_change,
                on_session_start=self._on_session_started,
                on_early_warning=self._on_early_warning,
                on_pause=self._on_session_paused,
                on_resume=self._on_session_resumed,
                on_stop=self._on_session_stopped,
            )

            # GUI setup
            self.root = tk.Tk()
            self.setup_window()
            self.create_widgets()
            self.apply_theme()
            self.setup_keyboard_shortcuts()

            # Mini indicator for minimized state
            self.mini_indicator = None
            self.setup_mini_indicator()

            # Check for crash-recovery state on startup (runs after GUI is shown)
            self.schedule_callback(200, self._check_crash_recovery)

            # Show task input dialog if no tasks exist for today
            self.schedule_callback(400, self.check_and_show_task_dialog)

            # Auto-manage the daemon in the background while the GUI is running
            self._auto_start_daemon()

            # Start update loop
            self.schedule_callback(100, self.update_loop)

        except Exception as e:
            print(f"[X] Error initializing GUI: {e}")
            import traceback

            traceback.print_exc()
            raise

    def setup_window(self):
        """Configure the main window"""
        self.root.title("FT")
        self.root.resizable(True, True)  # Enable resizing

        # Set minimum window size to prevent it from becoming too small
        self.root.minsize(250, 450)

        # Configure grid weights for proper expansion
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Load saved window dimensions or use defaults
        self.load_window_dimensions()

        # Bind minimize/restore events for mini indicator
        self.root.bind("<Unmap>", self.on_minimize)
        self.root.bind("<Map>", self.on_restore)
        # Show the mini indicator when the application loses focus (not only on minimize)
        self.root.bind("<FocusOut>", self.on_focus_out)
        self.root.bind("<FocusIn>", self.on_focus_in)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_window_dimensions(self):
        """Load saved window dimensions or use defaults"""
        try:
            saved_geometry = self.config.get("window_geometry", None)
            if saved_geometry and self._geometry_is_visible(saved_geometry):
                self.root.geometry(saved_geometry)
            else:
                self.center_window_default()
        except Exception:
            self.center_window_default()

    def _geometry_is_visible(self, geometry: str) -> bool:
        """Return True if the given geometry string places the window on a visible screen."""
        try:
            import ctypes
            import re

            m = re.match(r"(\d+)x(\d+)([\+\-][\+\-]?\d+)([\+\-]\d+)", geometry)
            if not m:
                return False
            win_w = int(m.group(1))
            # height from geometry not used
            # Strip leading '+' that Tkinter sometimes puts before a negative sign
            win_x = int(m.group(3).lstrip("+"))
            win_y = int(m.group(4).lstrip("+"))
            # Get virtual screen bounds (covers all monitors)
            k = ctypes.windll.user32
            vx = k.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            vy = k.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            vw = k.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            vh = k.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
            # At least 50px of width and 30px of the title bar must be on-screen
            return (
                win_x + win_w >= vx + 50
                and win_x <= vx + vw - 50
                and win_y >= vy
                and win_y <= vy + vh - 30
            )
        except Exception:
            return True  # If check fails, trust the saved value

    def center_window_default(self):
        """Center window with default dimensions"""
        # Default size optimized for compact usage
        default_width = 300
        default_height = 400

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
        except Exception:
            # Silently ignore save errors
            pass

    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Fixed sizes for consistent UI (no dynamic scaling)
        # Smaller base font sizes for more compact display (reduced further per user request)
        initial_sizes = {"title": 7, "time": 12, "normal": 5, "small": 4, "button": 5}
        initial_scaling = {
            "main_padding": 4,
            "frame_pady": 3,
            "button_padx": 1,
            "button_pady": 1,
            "progress_height": 12,
            "canvas_height": 80,
            "task_row_height": 18,
        }

        # Main frame with fixed padding
        self.main_frame = ttk.Frame(self.root, padding="4")
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

        # Playlist selection dropdown
        self.playlist_var = tk.StringVar()
        self.playlist_combo = ttk.Combobox(
            self.additional_frame,
            textvariable=self.playlist_var,
            state="readonly",
            width=20,
        )
        self.playlist_combo.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=(initial_scaling["button_pady"], 0),
            sticky=(tk.W, tk.E),
        )
        self.playlist_combo.bind("<<ComboboxSelected>>", self.on_playlist_change)

        # Load playlists into the dropdown
        self.load_playlists()

        # Music navigation: Prev | track name | Next
        self.music_nav_frame = ttk.Frame(self.additional_frame)
        self.music_nav_frame.grid(
            row=2,
            column=0,
            columnspan=3,
            pady=(initial_scaling["button_pady"], 0),
            sticky=(tk.W, tk.E),
        )
        self.music_nav_frame.grid_columnconfigure(0, weight=1)
        self.music_nav_frame.grid_columnconfigure(1, weight=3)
        self.music_nav_frame.grid_columnconfigure(2, weight=1)

        self.prev_track_button = ttk.Button(
            self.music_nav_frame,
            text="⏮",
            command=self.prev_track,
            style="Modern.TButton",
            width=3,
        )
        self.prev_track_button.grid(row=0, column=0, sticky=tk.E, padx=(0, 2))

        self.track_name_label = ttk.Label(
            self.music_nav_frame,
            text="",
            font=("Arial", 7),
            anchor="center",
        )
        self.track_name_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=2)

        self.next_track_button = ttk.Button(
            self.music_nav_frame,
            text="⏭",
            command=self.next_track,
            style="Modern.TButton",
            width=3,
        )
        self.next_track_button.grid(row=0, column=2, sticky=tk.W, padx=(2, 0))

        # Music status label
        self.music_status_label = ttk.Label(
            self.additional_frame,
            text="♪ Music Ready",
            font=("Arial", 7),
        )
        self.music_status_label.grid(
            row=3,
            column=0,
            columnspan=3,
            pady=(0, initial_scaling["button_pady"]),
        )

        # Task Management Section (Native Integration)
        self.create_task_section()

        # Initial display update after all widgets are created
        self.root.after(0, self.update_display)

    def create_task_section(self):
        """Create native task management section in the main GUI"""
        # Fixed scaling values - all keys needed throughout this method
        scaling = {
            "task_padding": 2,
            "small_pady": 1,
            "canvas_height": 70,
            "task_row_height": 18,
            "button_padx": 1,
            "button_pady": 1,
            "spinbox_width": 2,
            "small_button_width": 2,
            "frame_pady": 3,
            "main_padding": 4,
        }
        # Font sizes for the task area (increase to make tasks more readable)
        self.task_font_sizes = {
            "task_title": 10,
            "pomodoro": 10,
            "task_stats": 9,
            "entry": 9,
        }

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

        # Vim navigation state
        self.task_rows = []  # list of (task, frame) tuples — rebuilt each redraw
        self.selected_task_index = -1
        self._last_d_press = 0.0  # timestamp of previous 'd' for 'dd' detection

        # Drag-and-drop state
        self._drag_source_index = -1
        self._drag_ghost = None

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
            font=("Arial", self.task_font_sizes["task_stats"]),
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
            font=("Arial", self.task_font_sizes["entry"]),
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

        # Reset row tracker for vim navigation
        self.task_rows = []

        # Get tasks and stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        # Show/hide header elements based on state
        if stats["total"] > 0:
            # Show header with stats when there are tasks
            self.task_stats_label.grid(row=0, column=0, sticky=tk.W)
            # Minimal format: "2/5 🍅4/8"
            stats_text = (
                f"{stats['completed']}/{stats['total']} "
                f"🍅{stats['total_pomodoros_completed']}/"
                f"{stats['total_pomodoros_planned']}"
            )
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
        # Fixed scaling values
        scaling = {"small_pady": 1, "button_padx": 1, "small_button_width": 2}

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
        task_row.grid_columnconfigure(2, weight=1)  # Title column expands

        # Track this row for vim selection (index matches tasks list)
        self.task_rows.append((task, task_row))
        idx = len(self.task_rows) - 1

        # Apply selection highlight
        sel_bg = "#1a3a1a" if idx == self.selected_task_index else "#2b2b2b"
        try:
            task_row.configure(background=sel_bg)
        except Exception:
            pass

        sync_state = self.task_manager.get_sync_status(task.id)
        sync_icon_map = {
            "synced": "☁",
            "pending": "…",
            "error": "⚠",
            "disabled": "⏻",
            "local": "·",
        }
        sync_color_map = {
            "synced": "#00bfff",
            "pending": "#ffaa00",
            "error": "#ff5555",
            "disabled": "#666666",
            "local": "#666666",
        }
        sync_label = tk.Label(
            task_row,
            text=sync_icon_map.get(sync_state, "·"),
            font=("Arial", self.task_font_sizes["pomodoro"]),
            fg=sync_color_map.get(sync_state, "#666666"),
            bg=sel_bg,
        )
        sync_label.grid(row=0, column=0, padx=(0, scaling["small_pady"]))

        # Completion checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_row,
            variable=completed_var,
            command=lambda: self.toggle_task(task, completed_var),
        )
        check.grid(row=0, column=1, padx=(0, scaling["button_padx"]))

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
            font=("Arial", self.task_font_sizes["task_title"]),
            fg=text_color,
            bg=sel_bg,
            anchor="w",
        )
        title_label.grid(
            row=0, column=2, sticky=(tk.W, tk.E), padx=(0, scaling["small_pady"])
        )
        title_label.bind(
            "<Double-1>", lambda event, task=task: self.edit_task_title(event, task)
        )
        # Drag-and-drop bindings (drag the title label to reorder)
        title_label.bind("<ButtonPress-1>", lambda e, i=idx: self._drag_start(e, i))
        title_label.bind("<B1-Motion>", self._drag_motion)
        title_label.bind("<ButtonRelease-1>", self._drag_release)

        # Compact pomodoro progress
        pomodoro_text = f"{task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_color = "#00cc00" if task.pomodoros_completed > 0 else "#666666"

        pomodoro_label = tk.Label(
            task_row,
            text=pomodoro_text,
            font=("Arial", self.task_font_sizes["pomodoro"]),
            fg=pomodoro_color,
            bg=sel_bg,
        )
        pomodoro_label.grid(
            row=0, column=3, padx=(scaling["small_pady"], scaling["small_pady"])
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
                    column=4,
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
                    column=5,
                    padx=(scaling["small_pady"] // 2, scaling["small_pady"]),
                )
                delete_column = 6
            else:
                # Only add button when no completed pomodoros
                add_pomodoro_btn = ttk.Button(
                    task_row,
                    text="+",
                    command=lambda: self.add_pomodoro_to_task(task),
                    width=scaling["small_button_width"],
                )
                add_pomodoro_btn.grid(
                    row=0, column=4, padx=(scaling["small_pady"], scaling["small_pady"])
                )
                delete_column = 5
        else:
            delete_column = 4

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
        entry = ttk.Entry(
            event.widget.master, font=("Arial", self.task_font_sizes["entry"])
        )
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
        self.task_manager.toggle_task_completion(task.id)
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

    def sync_tasks_now(self):
        """Manually trigger a cloud sync (Ctrl+S)."""

        def _worker():
            summary = self.task_manager.sync_with_cloud()
            if self.google_integration and self.google_integration.is_enabled():
                message = (
                    "Sync complete "
                    f"(pushed {summary.get('pushed', 0)}, "
                    f"pulled {summary.get('pulled', 0)}, "
                    f"updated {summary.get('updated', 0)}, "
                    f"queued {summary.get('queued', 0)})"
                )
            else:
                message = (
                    f"Google sync offline. {summary.get('queued', 0)} change(s) queued."
                )

            def _notify():
                try:
                    messagebox.showinfo("Sync", message)
                except Exception:
                    logger.info(message)
                self.update_task_display()

            self._marshal(_notify)

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_add_task(self):
        """Public method to trigger adding a new task (for keyboard shortcuts)"""
        # Since the entry is always visible, just focus it
        self.task_entry.focus_set()
        if self.showing_placeholder:
            self.clear_placeholder()
            self.adding_task = True
            self.typing_active = True

    def is_typing(self):
        """Check if user is currently typing — true if any Entry/Text has focus."""
        try:
            focused = self.root.focus_get()
            return isinstance(focused, (tk.Entry, tk.Text))
        except Exception:
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
                    font=("Segoe UI", 7),
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
                    font=("Segoe UI", 7, "bold"),
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

        # D key - Delete last/selected task (dd = double-press)
        self.root.bind("<KeyPress-d>", lambda e: self.shortcut_delete_task())
        self.root.bind("<KeyPress-D>", lambda e: self.shortcut_delete_task())

        # J/K keys - Vim navigation (down/up through tasks)
        self.root.bind("<KeyPress-j>", lambda e: self._vim_nav_down())
        self.root.bind("<KeyPress-k>", lambda e: self._vim_nav_up())

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
        self.root.bind("<Key-j>", lambda e: self._vim_nav_down())
        self.root.bind("<Key-k>", lambda e: self._vim_nav_up())
        self.root.bind("<Control-s>", lambda e: self.sync_tasks_now())

        # Ensure the main window can receive focus for shortcuts
        self.root.focus_set()
        self.root.focus_force()

        # Set up a periodic focus refresh to ensure shortcuts always work
        # self.schedule_callback(1000, self.refresh_keyboard_focus)

    def refresh_keyboard_focus(self):
        """Periodically refresh keyboard focus to ensure shortcuts continue working"""
        try:
            # Only set focus if no widget currently has focus or if not typing
            focused_widget = self.root.focus_get()
            if not focused_widget or not self.typing_active:
                self.root.focus_set()
        except Exception:
            pass  # Ignore focus errors

        # Schedule next refresh
        # self.schedule_callback(2000, self.refresh_keyboard_focus)

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
        """Handle D key shortcut — first press arms, second press (dd) deletes selected."""
        if not self.is_typing():
            import time as _time

            now = _time.monotonic()
            if now - self._last_d_press < 0.5:
                # Double-d: delete selected task
                self._vim_delete_selected()
                self._last_d_press = 0.0
            else:
                self._last_d_press = now
            self.root.after(50, self.root.focus_set)

    # ── Vim navigation helpers ────────────────────────────────────────────────

    def _vim_nav_down(self):
        if self.is_typing():
            return
        tasks = self.task_manager.get_today_tasks()
        if not tasks:
            return
        self.selected_task_index = min(self.selected_task_index + 1, len(tasks) - 1)
        self._vim_refresh_highlight()

    def _vim_nav_up(self):
        if self.is_typing():
            return
        tasks = self.task_manager.get_today_tasks()
        if not tasks:
            return
        self.selected_task_index = max(self.selected_task_index - 1, 0)
        self._vim_refresh_highlight()

    def _vim_delete_selected(self):
        tasks = self.task_manager.get_today_tasks()
        if not tasks:
            return
        idx = self.selected_task_index
        if 0 <= idx < len(tasks):
            self.task_manager.delete_task(tasks[idx].id)
        else:
            # Fallback: delete first task
            self.task_manager.delete_task(tasks[0].id)
        # Adjust selection so it stays valid
        remaining = max(0, len(tasks) - 2)
        self.selected_task_index = min(self.selected_task_index, remaining)
        self.update_task_display()
        self.root.after(50, self.root.focus_set)

    def _vim_refresh_highlight(self):
        """Update row background colours to reflect current selection."""
        for i, (task, frame) in enumerate(self.task_rows):
            bg = "#1a3a1a" if i == self.selected_task_index else "#2b2b2b"
            try:
                frame.configure(background=bg)
                for child in frame.winfo_children():
                    try:
                        child.configure(background=bg)
                    except Exception:
                        pass
            except Exception:
                pass

    # ── Drag-and-drop helpers ─────────────────────────────────────────────────

    def _drag_start(self, event, index):
        self._drag_source_index = index

    def _drag_motion(self, event):
        pass  # Visual feedback could be added here

    def _drag_release(self, event):
        if self._drag_source_index < 0:
            return
        # Determine destination row from mouse y position
        src = self._drag_source_index
        dest = src
        for i, (task, frame) in enumerate(self.task_rows):
            try:
                fy = frame.winfo_y()
                fh = frame.winfo_height()
                # event.y_root relative to canvas
                canvas_y = event.y_root - self.tasks_canvas.winfo_rooty()
                if fy <= canvas_y < fy + fh:
                    dest = i
                    break
            except Exception:
                pass

        if src != dest:
            tasks = self.task_manager.get_today_tasks()
            if 0 <= src < len(tasks) and 0 <= dest < len(tasks):
                self.task_manager.reorder_tasks(tasks[src].id, dest)
                self.selected_task_index = dest
                self.update_task_display()
        self._drag_source_index = -1

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
            main_frame, text="📝 Task Manager", font=("Arial", 13, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Task management frame (reuse the same logic as main GUI)
        self.separate_task_frame = ttk.LabelFrame(
            main_frame, text="Current Tasks", padding="8"
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
            font=("Arial", 5),
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
            font=("Arial", 7),
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
            stats_text = (
                f"{stats['completed']}/{stats['total']} tasks "
                f"({completion_rate}%) | 🍅 "
                f"{stats['total_pomodoros_completed']}/"
                f"{stats['total_pomodoros_planned']}"
            )
            self.separate_stats_label.config(text=stats_text)
        else:
            self.separate_stats_label.config(text="No tasks yet")

        # Display tasks
        if not tasks:
            placeholder = tk.Label(
                self.separate_tasks_display,
                text="🎯 No tasks yet!\nAdd your first task above",
                font=("Arial", 10, "italic"),
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
            font=("Arial", 7),
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
            font=("Arial", 7),
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
            "Test Music",
            "This will play a short music sample for 5 seconds.\n\n"
            "Would you like to proceed with the music test?",
        )

        if result:
            self.music.start_music(volume=20)
            self.root.after(5000, lambda: self.music.stop_music())
            if hasattr(self, "music_status_label"):
                self.music_status_label.config(text="♪ Testing Music...")
            self.root.after(
                5500, lambda: self.music_status_label.config(text="♪ Test Complete")
            )

    def next_track(self):
        """Skip to next track in current playlist"""
        self.music.next_track()

    def prev_track(self):
        """Go to previous track in current playlist"""
        self.music.previous_track()

    def load_playlists(self):
        """Load playlists into the combobox."""
        self.playlists = self.config.get_music_playlists()
        playlist_names = [p["name"] for p in self.playlists]
        self.playlist_combo["values"] = playlist_names

        default_playlist_path = self.config.get("classical_music_default_playlist")
        if default_playlist_path:
            for p in self.playlists:
                if p["path"] == default_playlist_path:
                    self.playlist_var.set(p["name"])
                    return

        if playlist_names:
            self.playlist_var.set(playlist_names[0])
            # Also set this as the default in config if it's not set
            if not default_playlist_path:
                selected_playlist = next(
                    (p for p in self.playlists if p["name"] == playlist_names[0]), None
                )
                if selected_playlist:
                    self.config.set(
                        "classical_music_default_playlist", selected_playlist["path"]
                    )
                    self.config.save_config()

    def on_playlist_change(self, event=None):
        """Handle playlist selection change."""
        selected_name = self.playlist_var.get()
        selected_playlist = next(
            (p for p in self.playlists if p["name"] == selected_name), None
        )

        if selected_playlist:
            path = selected_playlist["path"]
            self.config.set("classical_music_default_playlist", path)
            self.config.set("classical_music_selected_playlist", path)
            self.config.save_config()

            if self.music.is_playing:
                # change_playlist stops cleanly then starts with the new path
                self.music.change_playlist(path)
            # If not playing, config update is enough; next start will use the new path

    def show_statistics(self):
        """Show session statistics"""
        stats = self.session_manager.get_session_statistics()

        stats_text = f"""Session Statistics:

Total Sessions: {stats["total_sessions"]}
Work Sessions: {stats["work_sessions"]}
Break Sessions: {stats["break_sessions"]}

Total Work Time: {stats["total_work_time"]:.1f} minutes
Total Break Time: {stats["total_break_time"]:.1f} minutes

Average Work Session: {stats["average_work_session"]:.1f} minutes
Average Break Session: {stats["average_break_session"]:.1f} minutes

Today's Sessions: {stats["today_sessions"]}
Today's Work Time: {stats["today_work_time"]:.1f} minutes"""

        messagebox.showinfo("Session Statistics", stats_text)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(
            self.root,
            self.config,
            google_integration=self.google_integration,
            task_manager=self.task_manager,
        )
        self.root.wait_window(dialog.dialog)

        self.config.load_config()
        self.task_manager.set_google_integration(
            self.google_integration,
            self.config.get("google_task_list_id", DEFAULT_TASK_LIST_ID),
        )
        self.work_button.config(
            text=f"Work Session ({self.config.get('work_mins')} min)"
        )
        self.short_break_button.config(
            text=f"Short Break ({self.config.get('short_break_mins')} min)"
        )
        self.long_break_button.config(
            text=f"Long Break ({self.config.get('long_break_mins')} min)"
        )
        self.update_task_display()

    def on_session_tick(self, elapsed_seconds: int, total_seconds: int):
        """Handle session timer tick"""
        # This will be called from update_loop to avoid threading issues
        pass

    def on_session_complete(self, session_type: SessionType, duration: int):
        """Handle session completion"""

        def _do():
            # Stop music when a work session ends (break is starting)
            if session_type == SessionType.WORK and self.config.get(
                "pause_music_on_break", True
            ):
                self.music.stop_music()
            self.notifications.show_session_complete(session_type.value, duration)
            self.tray.set_state("idle", "Focus Timer — Session complete")
            self._ensure_window_visible()
            self.update_display()
            self.update_button_states()
            self.show_completion_dialog(session_type, duration)

        self._marshal(_do)

    def _ensure_window_visible(self):
        """Ensure the main window is visible and focused"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(100, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except Exception:
            pass

    def on_session_state_change(self, old_state: SessionState, new_state: SessionState):
        """Handle session state changes — always marshal back to main thread."""

        def _do():
            try:
                self.update_display()
                self.update_button_states()
                if new_state in (
                    SessionState.COMPLETED,
                    SessionState.STOPPED,
                    SessionState.READY,
                ):
                    if self.mini_indicator and self.mini_indicator.winfo_exists():
                        self.mini_indicator.withdraw()
            except Exception:
                pass

        self._marshal(_do)

    # ── Session event handlers (called from timer thread — marshal to main) ───

    def _on_session_started(self, session_type: SessionType, duration_minutes: int):
        """Called when a new session begins — start music, show notification, update tray."""

        def _do():
            if session_type == SessionType.WORK and self.config.get(
                "classical_music", True
            ):
                self.music.start_music()
            self.notifications.show_session_start(session_type.value, duration_minutes)
            tray_state = "work" if session_type == SessionType.WORK else "break"
            self.tray.set_state(
                tray_state,
                f"Focus Timer — {session_type.value.replace('_', ' ').title()} ({duration_minutes}m)",
            )

        self._marshal(_do)

    def _on_early_warning(self, session_type: SessionType, minutes_remaining: int):
        """Show early-warning notification."""

        def _do():
            self.notifications.show_early_warning(session_type.value, minutes_remaining)

        self._marshal(_do)

    def _on_session_paused(self, session_type: SessionType):
        """Pause music when session is paused."""

        def _do():
            if session_type == SessionType.WORK:
                self.music.pause_music()
            self.tray.set_state("paused", "Focus Timer — Paused")

        self._marshal(_do)

    def _on_session_resumed(self, session_type: SessionType):
        """Resume music when session resumes."""

        def _do():
            if session_type == SessionType.WORK:
                self.music.resume_music()
            tray_state = "work" if session_type == SessionType.WORK else "break"
            self.tray.set_state(
                tray_state,
                f"Focus Timer — {session_type.value.replace('_', ' ').title()}",
            )

        self._marshal(_do)

    def _on_session_stopped(self, session_type: SessionType, elapsed_minutes: float):
        """Stop music on explicit stop."""

        def _do():
            self.music.stop_music()
            self.tray.set_state("idle", "Focus Timer — Idle")

        self._marshal(_do)

    def show_completion_dialog(self, session_type: SessionType, duration: int):
        """Show session completion dialog"""
        session_name = session_type.value.replace("_", " ").title()

        # For work sessions, allow task tracking
        if session_type == SessionType.WORK:
            self.show_work_completion_dialog(session_name, duration)
        else:
            self.show_break_completion_dialog(session_name, duration)

    def show_work_completion_dialog(self, session_name: str, duration: int):
        """Handle work session completion - auto-track to current task if set"""
        # Auto-track to current task if one is selected
        if self.current_task_id:
            self.task_manager.add_pomodoro_to_task(self.current_task_id)
            self.update_task_display()

        # Auto-start next session based on config
        if self.config.get("auto_start_break", True):
            delay_secs = self.config.get("auto_start_delay", 2) * 1000
            completed_work = self.session_manager.completed_work_sessions
            if completed_work % self.config.get("long_break_interval", 4) == 0:
                self.root.after(
                    delay_secs, lambda: self.start_session(SessionType.LONG_BREAK)
                )
            else:
                self.root.after(
                    delay_secs, lambda: self.start_session(SessionType.SHORT_BREAK)
                )

    def show_break_completion_dialog(self, session_name: str, duration: int):
        """Handle break session completion - auto-start work if configured"""
        # Auto-start work session based on config
        if self.config.get("auto_start_work", False):
            delay_secs = self.config.get("auto_start_delay", 2) * 1000
            self.root.after(delay_secs, lambda: self.start_session(SessionType.WORK))

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

        # Update track name label
        if hasattr(self, "track_name_label"):
            track = self.music.current_track_name
            if track:
                # Trim to ~20 chars so it fits in the small label
                display = track[:20] if len(track) > 20 else track
                self.track_name_label.config(text=display)
            else:
                self.track_name_label.config(text="")

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
            # Update mini indicator if visible
            if self.mini_indicator and self.mini_indicator.winfo_viewable():
                self.update_mini_indicator()
            self.schedule_callback(1000, self.update_loop)  # Update every second
        except Exception:
            pass  # Ignore errors if window is being destroyed

    def _check_crash_recovery(self):
        """Check for a crash-recovery state file and offer to resume."""
        saved = self.session_manager.load_saved_state()
        if not saved:
            return

        saved_at = saved.get("saved_at", "unknown time")
        elapsed = saved.get("elapsed_seconds", 0)
        session_type = saved.get("session_type", "work").replace("_", " ")
        elapsed_mins = elapsed // 60
        elapsed_secs = elapsed % 60

        answer = messagebox.askyesno(
            "Resume Session?",
            f"A session was interrupted on {saved_at[:16]}.\n\n"
            f"  Type     : {session_type.title()}\n"
            f"  Elapsed  : {elapsed_mins:02d}:{elapsed_secs:02d}\n\n"
            "Would you like to resume from where you left off?",
        )

        if answer:
            # Restore state: adjust session so remaining = saved remaining
            type_map = {v.value: v for v in SessionType}
            s_type = type_map.get(saved.get("session_type", "work"), SessionType.WORK)
            total = saved.get("session_duration", 0)
            elapsed_s = saved.get("elapsed_seconds", 0)
            remaining = max(1, total - elapsed_s)
            # Restart with remaining seconds as a fractional-minute session
            remaining_mins = max(1, round(remaining / 60))
            self.session_manager.start_session(s_type, remaining_mins)
            logger.info("Session resumed from crash-recovery state")
        else:
            self.session_manager.clear_saved_state()
            logger.info("Crash-recovery state discarded by user")

    def on_closing(self):
        """Handle application closing"""
        if self.mini_indicator:
            try:
                self.mini_indicator.destroy()
            except Exception:
                pass
            self.mini_indicator = None  # prevent stale ref in callbacks

        if self.daemon_manager:
            self.daemon_manager.stop(managed_only=True)

        self.cleanup_callbacks()
        self.save_window_dimensions()
        self.session_manager.cleanup()
        self.music.cleanup()
        self.hotkeys.stop()
        self.tray.stop()
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
            cb_id_ref = [None]

            def _wrapper():
                try:
                    self.scheduled_callbacks.remove(cb_id_ref[0])
                except ValueError:
                    pass
                callback()

            callback_id = self.root.after(delay, _wrapper)
            cb_id_ref[0] = callback_id
            self.scheduled_callbacks.append(callback_id)
            return callback_id
        except Exception:
            return None

    def _on_daemon_status_changed(self, status: str):
        """Handle daemon status changes"""

        def _do():
            if self.daemon_status_label:
                self.daemon_status_label.config(
                    text=self.daemon_manager.get_status_display()
                )

            # Update button states
            is_running = status == "running"
            if self.daemon_start_button:
                self.daemon_start_button.config(
                    state="disabled",
                    text="Auto Daemon ✔" if is_running else "Auto Daemon…",
                )
            if self.daemon_stop_button:
                self.daemon_stop_button.config(
                    state="normal" if is_running else "disabled"
                )

        self._marshal(_do)

    def _start_daemon_clicked(self):
        """Handle start daemon button click"""

        def _do():
            self.daemon_start_button.config(state="disabled", text="Starting...")
            if self.daemon_manager.start():
                messagebox.showinfo(
                    "Success",
                    "Daemon started successfully!\n\nYou can now use daemon features.",
                )
            else:
                messagebox.showerror("Error", "Failed to start daemon")
            self.daemon_start_button.config(state="disabled", text="Auto Daemon")

        self.schedule_callback(100, _do)

    def _stop_daemon_clicked(self):
        """Handle stop daemon button click"""

        def _do():
            self.daemon_stop_button.config(state="disabled", text="Stopping...")
            if self.daemon_manager.stop():
                messagebox.showinfo("Success", "Daemon stopped")
            else:
                messagebox.showerror("Error", "Failed to stop daemon")
            self.daemon_stop_button.config(state="normal", text="Stop Daemon")

        self.schedule_callback(100, _do)

    def _auto_start_daemon(self):
        """Start the daemon automatically in the background."""

        def _do():
            try:
                if self.daemon_manager.is_running():
                    self._on_daemon_status_changed("running")
                    return
                started = self.daemon_manager.start()
                self._on_daemon_status_changed("running" if started else "error")
                if not started:
                    logger.warning("Daemon auto-start failed")
            except Exception as exc:
                logger.warning("Daemon auto-start error: %s", exc)

        threading.Thread(target=_do, daemon=True).start()

    def _marshal(self, fn):
        """Schedule fn on the Tkinter event loop from any thread (fire-and-forget)."""
        try:
            self.root.after_idle(fn)
        except Exception:
            pass

    def _show_window(self) -> None:
        """Bring the main window to the foreground (safe to call from any thread)."""

        def _do():
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass

        self._marshal(_do)

    def cleanup_callbacks(self):
        """Cancel all scheduled callbacks to prevent threading errors"""
        for callback_id in self.scheduled_callbacks:
            try:
                self.root.after_cancel(callback_id)
            except Exception:
                pass
        self.scheduled_callbacks.clear()

    # ============== Mini Indicator Methods ==============

    def setup_mini_indicator(self):
        """Setup the mini floating indicator window"""
        self.mini_indicator = tk.Toplevel(self.root)
        self.mini_indicator.withdraw()  # Start hidden
        self.mini_indicator.overrideredirect(True)  # Borderless
        self.mini_indicator.attributes("-topmost", True)  # Always on top
        self.mini_indicator.attributes("-alpha", 0.9)  # Transparency
        self.mini_indicator.configure(bg="#1a1a2e")

        # Position in bottom-left corner of screen (was bottom-right)
        screen_height = self.root.winfo_screenheight()
        # Use small margins from the left and bottom edges for consistency
        left_margin = 10
        bottom_margin = 70
        self.mini_indicator.geometry(
            f"75x30+{left_margin}+{screen_height - bottom_margin}"
        )

        # Timer label - smaller font
        self.mini_time_label = tk.Label(
            self.mini_indicator,
            text="00:00",
            font=("Arial", 7, "bold"),
            fg="#ffffff",
            bg="#1a1a2e",
        )
        self.mini_time_label.pack(pady=(4, 2))

        # Session type indicator (colored bar using Canvas for reliable color)
        self.mini_status_bar = tk.Canvas(
            self.mini_indicator, height=5, bg="#3498db", highlightthickness=0
        )
        self.mini_status_bar.pack(fill="x", side="bottom")

        # Click to restore
        for widget in [
            self.mini_indicator,
            self.mini_time_label,
            self.mini_status_bar,
        ]:
            widget.bind("<Button-1>", self.restore_from_mini)

        # Drag support (right-click drag)
        for widget in [self.mini_indicator, self.mini_time_label, self.mini_status_bar]:
            widget.bind("<Button-3>", self.start_mini_drag)
            widget.bind("<B3-Motion>", self.do_mini_drag)

    def on_minimize(self, event=None):
        """Handle window minimize - show mini indicator"""
        if event and event.widget == self.root:
            # Show mini indicator only if a session is active
            if self.session_manager.state in [
                SessionState.RUNNING,
                SessionState.PAUSED,
            ]:
                self.update_mini_indicator()
                self.mini_indicator.deiconify()

    def on_restore(self, event=None):
        """Handle window restore - hide mini indicator"""
        if event and event.widget == self.root:
            if self.mini_indicator:
                self.mini_indicator.withdraw()

    def on_focus_out(self, event=None):
        """Handle application losing focus - show mini indicator if app loses focus

        We use after(50) to check the focus ownership (to avoid showing the mini
        indicator on quick internal focus changes between widgets).
        """
        try:
            # Delay slightly to allow focus changes to settle
            self.root.after(50, self._handle_focus_out)
        except Exception:
            pass

    def _handle_focus_out(self):
        try:
            # If no widget in the root has focus, consider the app unfocused
            if not self.root.focus_get():
                # Only show mini indicator if a session is active (running or paused)
                if self.session_manager.state in [
                    SessionState.RUNNING,
                    SessionState.PAUSED,
                ]:
                    if self.mini_indicator:
                        self.update_mini_indicator()
                        self.mini_indicator.deiconify()
        except Exception:
            pass

    def on_focus_in(self, event=None):
        """Handle application focus gained - hide mini indicator"""
        try:
            # Small delay to ensure focus is inside the app
            self.root.after(50, self._handle_focus_in)
        except Exception:
            pass

    def _handle_focus_in(self):
        try:
            # If any widget in the root has focus (app resumed), hide mini indicator
            if self.root.focus_get():
                if self.mini_indicator:
                    self.mini_indicator.withdraw()
        except Exception:
            pass

    def restore_from_mini(self, event=None):
        """Restore main window when mini indicator is clicked"""
        self.mini_indicator.withdraw()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def update_mini_indicator(self):
        """Update mini indicator display"""
        if not self.mini_indicator or not self.mini_indicator.winfo_exists():
            return

        # Update time and color based on session state
        info = self.session_manager.get_session_info()
        session_type = info.get("type", "")
        state = info.get("state", "")

        # Show time or ready state
        if state in ["ready", "stopped", "completed"]:
            self.mini_time_label.config(text="Ready")
            color = "#6c757d"  # Gray when idle
        else:
            time_text = self.session_manager.get_time_display()
            self.mini_time_label.config(text=time_text)

            if state == "paused":
                color = "#f39c12"  # Orange for paused
            elif "work" in session_type.lower():
                color = "#e74c3c"  # Red for work
            elif "long" in session_type.lower():
                color = "#2ecc71"  # Green for long break
            else:
                color = "#3498db"  # Blue for short break

        self.mini_status_bar.config(bg=color)

    def start_mini_drag(self, event):
        """Start dragging mini indicator"""
        self.mini_drag_x = event.x
        self.mini_drag_y = event.y

    def do_mini_drag(self, event):
        """Handle dragging mini indicator"""
        x = self.mini_indicator.winfo_x() + event.x - self.mini_drag_x
        y = self.mini_indicator.winfo_y() + event.y - self.mini_drag_y
        self.mini_indicator.geometry(f"+{x}+{y}")


def console_dashboard(period: str = "week", export: bool = False):
    """Run console version of the dashboard"""
    analyzer = SessionAnalyzer()
    sessions = analyzer.filter_sessions(period)
    stats = analyzer.calculate_stats(sessions)
    daily_df = analyzer.get_daily_breakdown(sessions)

    # Console output with enhanced formatting
    print("═" * 70)
    print("                🎯 FOCUS PRODUCTIVITY DASHBOARD")
    print("═" * 70)
    print()

    print(f"📊 SUMMARY ({period.upper()})")
    print(f"├─ Total Sessions: {stats['total_sessions']}")
    print(f"├─ Work Sessions: {stats['work_sessions']}")
    print(f"├─ Break Sessions: {stats['break_sessions']}")
    print(f"├─ Productive Hours: {stats['productive_hours']}")
    print(f"├─ Days Active: {stats['days_active']}")
    print(f"├─ Current Streak: {stats['streak_days']} days")
    print(f"├─ Avg Work Session: {stats['avg_work_session']} min")
    print(f"└─ Avg Break Session: {stats['avg_break_session']} min")
    print()

    if stats["total_sessions"] > 0:
        print("📈 PRODUCTIVITY METRICS")
        print(f"├─ Work/Break Ratio: {stats['work_ratio']}% work")
        print(f"├─ Total Focus Time: {stats['total_work_time']} minutes")
        print(f"├─ Total Break Time: {stats['total_break_time']} minutes")
        print(f"├─ Avg Sessions/Day: {stats['avg_sessions_per_day']}")
        print(f"└─ Avg Work/Day: {stats['avg_work_per_day']} minutes")
        print()

    if not daily_df.empty:
        print("📅 DAILY BREAKDOWN (Recent)")
        for _, row in daily_df.head(7).iterrows():
            date_str = row["Date"].strftime("%a, %b %d")
            bar = "█" * min(20, int(row["Work Hours"] * 2))
            print(
                f"├─ {date_str}: {row['Work Sessions']} sessions, {row['Work Hours']}h {bar}"
            )
        print()

    # Enhanced insights
    print("💡 PRODUCTIVITY INSIGHTS")
    if stats["total_sessions"] == 0:
        print("├─ No sessions recorded yet. Start your first focus session!")
    elif stats["productive_hours"] < 2:
        print("├─ Building momentum! Try to reach 2+ hours of focus time daily.")
    elif stats["productive_hours"] < 4:
        print("├─ Good progress! You're developing a solid focus habit.")
    else:
        print("├─ Excellent focus! You're in the productivity zone! 🔥")

    if stats["streak_days"] >= 7:
        print(f"├─ Amazing {stats['streak_days']}-day streak! Consistency is key! 🏆")
    elif stats["streak_days"] >= 3:
        print(f"├─ Great {stats['streak_days']}-day streak! Keep it going! 💪")
    elif stats["streak_days"] == 0:
        print("├─ Ready to start a new streak? Today is perfect! ⭐")

    print("└─ Remember: Consistency beats perfection! 🎯")
    print()
    print("═" * 70)

    if export:
        export_path = analyzer.export_data(sessions, stats, daily_df)
        print(f"📁 Data exported to: {export_path}")

    return analyzer, sessions, stats, daily_df


def check_dependencies():
    """Check if all required dependencies are available"""
    optional_modules = {
        "yaml": "PyYAML",
        "matplotlib": "matplotlib",
        "pandas": "pandas",
        "seaborn": "seaborn",
        "plyer": "plyer",
    }

    missing_deps = [
        friendly_name
        for module_name, friendly_name in optional_modules.items()
        if importlib.util.find_spec(module_name) is None
    ]

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
    parser.add_argument("--gui", action="store_true", help="Launch GUI timer directly")
    parser.add_argument(
        "--console", action="store_true", help="Launch console timer directly"
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Launch analytics dashboard directly"
    )
    parser.add_argument(
        "--launcher", action="store_true", help="Show launcher GUI (default)"
    )

    # Quick start options
    parser.add_argument(
        "--work",
        type=int,
        metavar="MINUTES",
        help="Start a work session for specified minutes (console mode)",
    )
    parser.add_argument(
        "--break-session",
        type=int,
        metavar="MINUTES",
        dest="break_session",
        help="Start a break session for specified minutes (console mode)",
    )
    parser.add_argument(
        "--pomodoro",
        action="store_true",
        help="Start a standard 25-minute Pomodoro session (console mode)",
    )

    # Configuration
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument(
        "--check-deps", action="store_true", help="Check dependencies and exit"
    )

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
        if args.work or args.break_session or args.pomodoro:
            if ConsoleInterface is None:
                print("❌ Console interface not available.")
                sys.exit(1)
            console = ConsoleInterface(args.config)
            if args.work:
                console.run_command("start", args.work, "work")
            elif args.break_session:
                console.run_command("start", args.break_session, "short_break")
            elif args.pomodoro:
                console.run_command("start", 25, "work")

        # Handle direct mode launches
        elif args.gui:
            gui = FocusGUI()
            gui.run()

        elif args.console:
            if ConsoleInterface is None:
                print("❌ Console interface not available.")
                sys.exit(1)
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
