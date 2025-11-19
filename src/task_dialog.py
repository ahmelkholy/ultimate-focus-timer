#!/usr/bin/env python3
"""
Daily Tasks Dialog for Ultimate Focus Timer
Dialog for adding and managing daily tasks
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from task_manager import Task, TaskManager


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
            text="📝 What are your tasks for today?",
            font=("Arial", 14, "bold"),
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)

        # Existing tasks frame (if any)
        existing_tasks = self.task_manager.get_today_tasks()
        if existing_tasks:
            existing_frame = ttk.LabelFrame(
                main_frame, text="Existing Tasks", padding="5"
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
                    font=("Arial", 9),
                    foreground="gray" if task.completed else "black",
                )
                task_label.grid(row=0, column=1, sticky=tk.W)

                # Pomodoro count
                pomodoro_text = (
                    f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
                )
                pomodoro_label = ttk.Label(
                    task_frame, text=pomodoro_text, font=("Arial", 8)
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
            # Uncomplete the task
            task.completed = False
            task.completed_at = None
            self.task_manager.save_tasks()

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
        self.frame = ttk.LabelFrame(parent, text="📝 Today's Tasks", padding="5")
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
        self.stats_label = ttk.Label(header_frame, text="", font=("Arial", 8))
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
            self.stats_label.config(text="No tasks for today")

        # Display tasks
        if not tasks:
            no_tasks_label = ttk.Label(
                self.tasks_container,
                text="Click 'Manage' to add your first task! 🎯",
                font=("Arial", 9, "italic"),
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
            font=("Arial", 9),
            foreground="gray" if task.completed else "black",
        )
        title_label.grid(row=0, column=1, sticky=tk.W)

        # Pomodoro progress
        pomodoro_text = f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_label = ttk.Label(task_frame, text=pomodoro_text, font=("Arial", 8))
        pomodoro_label.grid(row=0, column=2, padx=(5, 0))

    def toggle_task(self, task: Task, var: tk.BooleanVar):
        """Toggle task completion"""
        if var.get():
            self.task_manager.complete_task(task.id)
        else:
            # Uncomplete the task
            task.completed = False
            task.completed_at = None
            self.task_manager.save_tasks()

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
