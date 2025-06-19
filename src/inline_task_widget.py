#!/usr/bin/env python3
"""
Inline Task Widget for Ultimate Focus Timer
Simple task management directly in the main GUI
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from task_manager import Task, TaskManager


class InlineTaskWidget:
    """Inline task management widget for the main GUI"""

    def __init__(self, parent, task_manager: TaskManager):
        """Initialize the inline task widget"""
        self.parent = parent
        self.task_manager = task_manager
        self.adding_task = False
        self.typing_active = False

        # Create main frame with dark styling
        self.frame = ttk.LabelFrame(parent, text="📝 Today's Tasks", padding="8")
        self.create_widgets()
        self.apply_dark_theme()
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
            font=("Arial", 9),
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
        except:
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

        # Get tasks and stats
        tasks = self.task_manager.get_today_tasks()
        stats = self.task_manager.get_task_stats()

        # Update stats label
        if stats["total"] > 0:
            completion_rate = int(stats["completion_rate"])
            stats_text = f"Progress: {stats['completed']}/{stats['total']} tasks ({completion_rate}%) | 🍅 {stats['total_pomodoros_completed']}/{stats['total_pomodoros_planned']}"
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
                font=("Arial", 10, "italic"),
                fg="#666666",  # Gray text
                bg="#2b2b2b",  # Dark background
                justify="center",
            )
            placeholder_label.pack()
        elif tasks:
            # Show tasks
            for i, task in enumerate(tasks):
                self.create_task_row(self.tasks_container, task, i)

    def on_canvas_configure(self, event):
        """Handle canvas resize to update task container width"""
        # Set the width of the tasks_container to match the canvas width
        canvas_width = event.width
        if hasattr(self, "canvas_window_id"):
            self.tasks_canvas.itemconfig(self.canvas_window_id, width=canvas_width)

    def create_task_row(self, parent, task: Task, row: int):
        """Create a row for displaying a task"""
        task_frame = ttk.Frame(parent)
        task_frame.grid(
            row=row, column=0, sticky=(tk.W, tk.E), pady=1, padx=0
        )  # Remove padding to maximize width

        # Configure the task frame to fill available width
        parent.grid_columnconfigure(0, weight=1)  # Ensure parent expands column 0
        task_frame.grid_columnconfigure(
            1, weight=1
        )  # Make title column expand to fill space

        # Completion checkbox
        completed_var = tk.BooleanVar(value=task.completed)
        check = ttk.Checkbutton(
            task_frame,
            variable=completed_var,
            command=lambda: self.toggle_task(task, completed_var),
        )
        check.grid(row=0, column=0, padx=(0, 4))  # Small padding after checkbox

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
            font=("Arial", 10),
            fg=text_color,
            bg="#2b2b2b",  # Dark background
            anchor="w",
            justify="left",
        )
        title_label.grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 1)
        )  # Minimal padding for maximum width

        # Pomodoro progress with green color
        pomodoro_text = f"🍅 {task.pomodoros_completed}/{task.pomodoros_planned}"
        pomodoro_color = "#00cc00" if task.pomodoros_completed > 0 else "#666666"

        pomodoro_label = tk.Label(
            task_frame,
            text=pomodoro_text,
            font=("Arial", 9),
            fg=pomodoro_color,
            bg="#2b2b2b",
        )
        pomodoro_label.grid(row=0, column=2, padx=(1, 1))  # Minimal padding

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

    def toggle_task(self, task: Task, var: tk.BooleanVar):
        """Toggle task completion"""
        if var.get():
            self.task_manager.complete_task(task.id)
            # Show congratulations for completed task
            self.show_task_completion_message(task)
        else:
            # Uncomplete the task
            task.completed = False
            task.completed_at = None
            self.task_manager.save_tasks()

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
            result = messagebox.askyesno(
                "No Tasks Found",
                "You don't have any tasks for today.\n\n"
                "Would you like to add some tasks to help you stay focused during your Pomodoro sessions?",
                parent=self.parent,
            )

            if result:
                self.show_add_task_entry()
                return False  # Don't start session yet
            else:
                # User chose to proceed without tasks
                return True

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
        except:
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
            except:
                pass  # Ignore focus errors

        return typing_state
