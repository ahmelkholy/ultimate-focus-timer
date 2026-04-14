import json
import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path

from src.core import TaskManager
from src.google_integration import GoogleIntegration, SCOPES


class StubGoogleIntegration:
    def __init__(self, remote_tasks=None):
        self.remote_tasks = remote_tasks or []
        self.created = []
        self.updated = []
        self.deleted = []

    def is_enabled(self):
        return True

    def fetch_remote_tasks(self, task_list_id, include_completed=True):
        return list(self.remote_tasks)

    def create_task(self, task_list_id, title, notes="", due=None):
        google_id = f"created-{len(self.created) + 1}"
        self.created.append(
            {
                "task_list_id": task_list_id,
                "title": title,
                "notes": notes,
                "due": due,
                "id": google_id,
            }
        )
        return {"id": google_id}

    def update_task(
        self, task_list_id, task_id, title=None, notes=None, completed=None
    ):
        self.updated.append(
            {
                "task_list_id": task_list_id,
                "task_id": task_id,
                "title": title,
                "notes": notes,
                "completed": completed,
            }
        )
        return {"id": task_id}

    def delete_task(self, task_list_id, task_id):
        self.deleted.append({"task_list_id": task_list_id, "task_id": task_id})
        return True


def write_tasks(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_install_credentials_content_saves_valid_json(tmp_path):
    integration = GoogleIntegration(tmp_path)

    saved_path = integration.install_credentials_content(
        json.dumps(
            {
                "installed": {
                    "client_id": "client-id",
                    "project_id": "project-id",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_secret": "client-secret",
                    "redirect_uris": ["http://localhost"],
                }
            }
        )
    )

    saved_payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved_path == tmp_path / "google_credentials.json"
    assert saved_payload["installed"]["client_id"] == "client-id"


def test_load_tasks_carries_forward_incomplete_tasks(tmp_path):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    write_tasks(
        tmp_path / "daily_tasks.json",
        {
            yesterday: [
                {
                    "id": f"{yesterday}_carry",
                    "title": "Carry me forward",
                    "description": "",
                    "completed": False,
                    "pomodoros_planned": 1,
                    "pomodoros_completed": 0,
                    "created_at": f"{yesterday}T10:00:00",
                    "completed_at": None,
                },
                {
                    "id": f"{yesterday}_done",
                    "title": "Keep me in history",
                    "description": "",
                    "completed": True,
                    "pomodoros_planned": 1,
                    "pomodoros_completed": 1,
                    "created_at": f"{yesterday}T09:00:00",
                    "completed_at": f"{yesterday}T11:00:00",
                },
            ],
            today: [],
        },
    )

    manager = TaskManager(data_dir=tmp_path)

    today_task_ids = [task.id for task in manager.get_today_tasks()]
    assert f"{yesterday}_carry" in today_task_ids
    assert f"{yesterday}_done" not in today_task_ids
    assert [task.id for task in manager.tasks[yesterday]] == [f"{yesterday}_done"]


def test_sync_with_cloud_pulls_remote_incomplete_tasks_into_current_tasks(tmp_path):
    remote_updated = (datetime.now() - timedelta(days=3)).isoformat()
    integration = StubGoogleIntegration(
        remote_tasks=[
            {
                "id": "remote-1",
                "title": "Remote task",
                "notes": "from google",
                "status": "needsAction",
                "updated": remote_updated,
            }
        ]
    )
    manager = TaskManager(
        data_dir=tmp_path,
        google_integration=integration,
        google_task_list_id="@default",
    )

    summary = manager.sync_with_cloud()

    assert summary["pulled"] == 1
    assert any(task.google_id == "remote-1" for task in manager.get_today_tasks())


def test_sync_with_cloud_updates_local_task_from_newer_remote_changes(tmp_path):
    today = datetime.now().strftime("%Y-%m-%d")
    write_tasks(
        tmp_path / "daily_tasks.json",
        {
            today: [
                {
                    "id": f"{today}_local",
                    "title": "Local title",
                    "google_id": "remote-2",
                    "description": "local",
                    "completed": False,
                    "pomodoros_planned": 1,
                    "pomodoros_completed": 0,
                    "created_at": f"{today}T08:00:00",
                    "updated_at": f"{today}T08:00:00",
                    "completed_at": None,
                }
            ]
        },
    )
    integration = StubGoogleIntegration(
        remote_tasks=[
            {
                "id": "remote-2",
                "title": "Remote title",
                "notes": "remote notes",
                "status": "completed",
                "updated": f"{today}T10:00:00",
                "completed": f"{today}T10:00:00",
            }
        ]
    )
    manager = TaskManager(
        data_dir=tmp_path,
        google_integration=integration,
        google_task_list_id="@default",
    )

    summary = manager.sync_with_cloud()
    task = manager.get_task_by_id(f"{today}_local")

    assert summary["updated"] == 1
    assert task is not None
    assert task.title == "Remote title"
    assert task.description == "remote notes"
    assert task.completed is True


def test_ui_module_has_google_browser_setup_dependencies():
    for module_name in (
        "src.ui",
        "matplotlib.pyplot",
        "matplotlib.backends.backend_tkagg",
        "pandas",
        "seaborn",
    ):
        sys.modules.pop(module_name, None)

    ui = importlib.import_module("src.ui")

    assert hasattr(ui, "webbrowser")
    assert ui.GOOGLE_OAUTH_SETUP_URL.startswith("https://")
    assert "matplotlib.pyplot" not in sys.modules
    assert "pandas" not in sys.modules
    assert "seaborn" not in sys.modules


def test_sync_with_cloud_pushes_newer_local_completion_to_google(tmp_path):
    today = datetime.now().strftime("%Y-%m-%d")
    write_tasks(
        tmp_path / "daily_tasks.json",
        {
            today: [
                {
                    "id": f"{today}_local_complete",
                    "title": "Finish spec",
                    "google_id": "remote-3",
                    "description": "done locally",
                    "completed": True,
                    "pomodoros_planned": 1,
                    "pomodoros_completed": 1,
                    "created_at": f"{today}T08:00:00",
                    "updated_at": f"{today}T10:00:00",
                    "completed_at": f"{today}T10:00:00",
                }
            ]
        },
    )
    integration = StubGoogleIntegration(
        remote_tasks=[
            {
                "id": "remote-3",
                "title": "Finish spec",
                "notes": "not done yet",
                "status": "needsAction",
                "updated": f"{today}T08:30:00",
            }
        ]
    )
    manager = TaskManager(
        data_dir=tmp_path,
        google_integration=integration,
        google_task_list_id="@default",
    )

    summary = manager.sync_with_cloud()

    assert summary["updated"] == 1
    assert integration.updated
    assert integration.updated[-1]["task_id"] == "remote-3"
    assert integration.updated[-1]["completed"] is True


def test_google_integration_requests_tasks_scope_only():
    assert SCOPES == ["https://www.googleapis.com/auth/tasks"]


def test_google_integration_status_includes_last_error(tmp_path):
    integration = GoogleIntegration(tmp_path)

    integration._set_last_error("Tasks API disabled", "https://console.example.com")
    status = integration.get_connection_status()

    assert status["last_error"] == "Tasks API disabled"
    assert status["last_error_help_url"] == "https://console.example.com"


def test_task_list_display_prefers_title_and_handles_duplicates():
    from src.ui import SettingsDialog

    options = {"Primary task list": "@default"}

    first = SettingsDialog._task_list_display("Work", "list-1", options)
    options[first] = "list-1"
    second = SettingsDialog._task_list_display("Work", "list-2", options)

    assert first == "Work"
    assert second == "Work (list-2)"
