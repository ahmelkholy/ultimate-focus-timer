#!/usr/bin/env python3
"""
Task Manager for Ultimate Focus Timer.
Manages daily tasks and integrates with Pomodoro sessions.
"""

import json
import logging
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from .app_paths import DATA_DIR, TASKS_FILE

logger = logging.getLogger(__name__)


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
    """Manages daily tasks for the focus timer.

    File writes are performed in a background thread to avoid blocking
    the Tkinter main loop.  A threading.Lock serialises concurrent writes.
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "daily_tasks.json" if data_dir else TASKS_FILE
        self.tasks: Dict[str, List[Task]] = {}
        self._lock = threading.Lock()
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
                for date_key, task_list in data.items():
                    self.tasks[date_key] = [
                        Task.from_dict(task_data) for task_data in task_list
                    ]
            except (json.JSONDecodeError, Exception):
                logger.exception("Error loading tasks from %s", self.tasks_file)
                self.tasks = {}

    def save_tasks(self):
        """Persist tasks to disk asynchronously (non-blocking)."""
        # Snapshot the data while holding the lock so background thread gets
        # a consistent view even if in-memory state changes concurrently.
        with self._lock:
            data = {
                date_key: [t.to_dict() for t in task_list]
                for date_key, task_list in self.tasks.items()
            }
        threading.Thread(target=self._write_tasks, args=(data,), daemon=True).start()

    def _write_tasks(self, data: dict):
        """Write serialised tasks to disk — runs in background thread."""
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError:
            logger.exception("Error saving tasks to %s", self.tasks_file)

    def get_today_tasks(self) -> List[Task]:
        """Get tasks for today"""
        today_key = self.get_today_key()
        return self.tasks.get(today_key, [])

    def add_task(
        self, title: str, description: str = "", pomodoros_planned: int = 1
    ) -> Task:
        """Add a new task for today"""
        today_key = self.get_today_key()

        # Use microsecond timestamp to avoid ID collisions from rapid additions
        task_id = f"{today_key}_{datetime.now().strftime('%H%M%S%f')}"

        task = Task(
            id=task_id,
            title=title,
            description=description,
            pomodoros_planned=pomodoros_planned,
        )

        if today_key not in self.tasks:
            self.tasks[today_key] = []

        # Insert at the beginning to show new tasks at top
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
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            keys_to_remove = [key for key in self.tasks if key < cutoff_str]
            for key in keys_to_remove:
                del self.tasks[key]
            if keys_to_remove:
                logger.info(
                    "Removed %d old task day(s) before %s",
                    len(keys_to_remove),
                    cutoff_str,
                )
                self.save_tasks()
        except Exception:
            logger.exception("Error cleaning up old tasks")
