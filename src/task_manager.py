#!/usr/bin/env python3
"""
Task Manager for Ultimate Focus Timer
Manages daily tasks and integrates with Pomodoro sessions
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Task:
    """Represents a daily task"""

    id: str
    title: str
    description: str = ""
    completed: bool = False
    pomodoros_planned: int = 1
    pomodoros_completed: int = 0
    created_at: str = ""
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def mark_complete(self):
        """Mark task as completed"""
        self.completed = True
        self.completed_at = datetime.now().isoformat()

    def add_pomodoro(self):
        """Add a completed pomodoro to this task"""
        self.pomodoros_completed += 1

    def remove_pomodoro(self):
        """Remove a completed pomodoro from this task"""
        if self.pomodoros_completed > 0:
            self.pomodoros_completed -= 1

    def to_dict(self) -> Dict:
        """Convert task to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        """Create task from dictionary"""
        return cls(**data)


class TaskManager:
    """Manages daily tasks for the focus timer"""

    def __init__(self, data_dir: str = None):
        """Initialize task manager"""
        if data_dir is None:
            # Use a consistent absolute path for all sessions
            # This ensures tasks persist across different working directories
            script_dir = Path(
                __file__
            ).parent.parent  # Go up from src/ to the project root
            self.data_dir = script_dir / "data"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / "daily_tasks.json"
        self.tasks: Dict[str, List[Task]] = {}
        self.load_tasks()

    def get_today_key(self) -> str:
        """Get today's date as a key"""
        return datetime.now().strftime("%Y-%m-%d")

    def load_tasks(self):
        """Load tasks from file"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Convert dictionaries back to Task objects
                for date_key, task_list in data.items():
                    self.tasks[date_key] = [
                        Task.from_dict(task_data) for task_data in task_list
                    ]
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading tasks: {e}")
                self.tasks = {}

    def save_tasks(self):
        """Save tasks to file"""
        try:
            # Convert Task objects to dictionaries
            data = {}
            for date_key, task_list in self.tasks.items():
                data[date_key] = [task.to_dict() for task in task_list]

            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def get_today_tasks(self) -> List[Task]:
        """Get tasks for today"""
        today_key = self.get_today_key()
        return self.tasks.get(today_key, [])

    def add_task(
        self, title: str, description: str = "", pomodoros_planned: int = 1
    ) -> Task:
        """Add a new task for today"""
        today_key = self.get_today_key()

        # Generate unique ID
        task_id = f"{today_key}_{len(self.get_today_tasks()) + 1}"

        task = Task(
            id=task_id,
            title=title,
            description=description,
            pomodoros_planned=pomodoros_planned,
        )

        if today_key not in self.tasks:
            self.tasks[today_key] = []

        # Insert at the beginning instead of append to show new tasks at top
        self.tasks[today_key].insert(0, task)
        self.save_tasks()
        return task

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed"""
        task = self.get_task_by_id(task_id)
        if task:
            task.mark_complete()
            self.save_tasks()
            return True
        return False

    def add_pomodoro_to_task(self, task_id: str) -> bool:
        """Add a completed pomodoro to a task"""
        task = self.get_task_by_id(task_id)
        if task:
            task.add_pomodoro()
            self.save_tasks()
            return True
        return False

    def remove_pomodoro_from_task(self, task_id: str) -> bool:
        """Remove a completed pomodoro from a task"""
        task = self.get_task_by_id(task_id)
        if task and task.pomodoros_completed > 0:
            task.remove_pomodoro()
            self.save_tasks()
            return True
        return False

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID"""
        today_tasks = self.get_today_tasks()
        for task in today_tasks:
            if task.id == task_id:
                return task
        return None

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        today_key = self.get_today_key()
        if today_key in self.tasks:
            self.tasks[today_key] = [
                task for task in self.tasks[today_key] if task.id != task_id
            ]
            self.save_tasks()
            return True
        return False

    def update_task_title(self, task_id: str, new_title: str) -> bool:
        """Update the title of a task."""
        task = self.get_task_by_id(task_id)
        if task:
            task.title = new_title
            self.save_tasks()
            return True
        return False

    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks for today"""
        return [task for task in self.get_today_tasks() if not task.completed]

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks for today"""
        return [task for task in self.get_today_tasks() if task.completed]

    def get_task_stats(self) -> Dict:
        """Get task completion statistics for today"""
        tasks = self.get_today_tasks()
        if not tasks:
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "completion_rate": 0,
                "total_pomodoros_planned": 0,
                "total_pomodoros_completed": 0,
            }

        completed = len(self.get_completed_tasks())
        total = len(tasks)

        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "total_pomodoros_planned": sum(task.pomodoros_planned for task in tasks),
            "total_pomodoros_completed": sum(
                task.pomodoros_completed for task in tasks
            ),
        }

    def has_tasks_for_today(self) -> bool:
        """Check if there are any tasks for today"""
        return len(self.get_today_tasks()) > 0

    def cleanup_old_tasks(self, days_to_keep: int = 30):
        """Clean up tasks older than specified days"""
        try:
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")

            # Remove old task entries
            keys_to_remove = [key for key in self.tasks.keys() if key < cutoff_str]

            for key in keys_to_remove:
                del self.tasks[key]

            if keys_to_remove:
                self.save_tasks()

        except Exception as e:
            print(f"Error cleaning up old tasks: {e}")
