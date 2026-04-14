#!/usr/bin/env python3
"""
google_integration.py - Google Tasks and Calendar integration for Ultimate Focus Timer.

Connects the local task list with Google Tasks and Google Calendar.
"""

import logging
import os
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Google API libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API libraries not installed. Google integration disabled.")


# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar",
]

DEFAULT_TASK_LIST_ID = "@default"


class GoogleIntegration:
    """Manages Google Tasks and Calendar integration"""

    def __init__(self, config_dir: Path):
        """Initialize Google integration"""
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.credentials_file = self.config_dir / "google_credentials.json"
        self.token_file = self.config_dir / "google_token.pickle"

        self.creds: Optional[Credentials] = None
        self.tasks_service = None
        self.calendar_service = None

        self.enabled = False

        if GOOGLE_API_AVAILABLE:
            self._load_credentials()

    def _load_credentials(self) -> bool:
        """Load or refresh Google credentials"""
        try:
            # Load token if it exists
            if self.token_file.exists():
                with open(self.token_file, "rb") as token:
                    self.creds = pickle.load(token)

            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Refreshing Google credentials...")
                    self.creds.refresh(Request())
                else:
                    # Need to authenticate
                    if not self.credentials_file.exists():
                        logger.warning(
                            f"Google credentials file not found: {self.credentials_file}"
                        )
                        return False

                    logger.info("Authenticating with Google...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials
                with open(self.token_file, "wb") as token:
                    pickle.dump(self.creds, token)

            # Build services
            self.tasks_service = build("tasks", "v1", credentials=self.creds)
            self.calendar_service = build("calendar", "v3", credentials=self.creds)
            self.enabled = True

            logger.info("Google integration enabled")
            return True

        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            self.enabled = False
            return False

    def is_enabled(self) -> bool:
        """Check if Google integration is enabled"""
        return self.enabled and GOOGLE_API_AVAILABLE

    def _execute_with_backoff(
        self, action: str, func: Callable[[], Any], retries: int = 3
    ) -> Any:
        """Run Google API call with simple exponential backoff for transient errors."""
        delay = 1.0
        for attempt in range(retries):
            try:
                return func()
            except HttpError as exc:
                status_code = getattr(getattr(exc, "resp", None), "status", None)
                if status_code in (429, 500, 503) and attempt < retries - 1:
                    logger.warning(
                        "%s throttled (%s); retrying in %.1fs",
                        action,
                        status_code,
                        delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, 30.0)
                    continue
                logger.error("%s failed: %s", action, exc)
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("%s failed unexpectedly: %s", action, exc)
                raise
        return None

    def get_task_lists(self) -> List[Dict[str, str]]:
        """Get all Google Tasks lists"""
        if not self.is_enabled():
            return []

        try:
            results = self._execute_with_backoff(
                "list_task_lists", lambda: self.tasks_service.tasklists().list().execute()
            )
            task_lists = results.get("items", [])
            return [{"id": tl["id"], "title": tl["title"]} for tl in task_lists]
        except HttpError as e:
            logger.error(f"Failed to get task lists: {e}")
            return []

    def get_tasks(self, task_list_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks from a specific Google Tasks list"""
        if not self.is_enabled():
            return []

        try:
            results = self._execute_with_backoff(
                "list_tasks",
                lambda: (
                    self.tasks_service.tasks()
                    .list(
                        tasklist=task_list_id or DEFAULT_TASK_LIST_ID,
                        showCompleted=False,
                        showHidden=False,
                    )
                    .execute()
                ),
            )
            tasks = results.get("items", [])
            return tasks
        except HttpError as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    def create_task(
        self, task_list_id: str, title: str, notes: str = "", due: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new task in Google Tasks"""
        if not self.is_enabled():
            return None

        try:
            task = {"title": title}

            if notes:
                task["notes"] = notes

            if due:
                # Google Tasks uses RFC 3339 format for due dates
                task["due"] = due.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            result = self._execute_with_backoff(
                "create_task",
                lambda: (
                    self.tasks_service.tasks()
                    .insert(tasklist=task_list_id or DEFAULT_TASK_LIST_ID, body=task)
                    .execute()
                ),
            )
            logger.info(f"Created Google task: {title}")
            return result
        except HttpError as e:
            logger.error(f"Failed to create task: {e}")
            return None

    def update_task(
        self,
        task_list_id: str,
        task_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a task in Google Tasks"""
        if not self.is_enabled():
            return None

        try:
            # Get current task
            task = self._execute_with_backoff(
                "get_task",
                lambda: (
                    self.tasks_service.tasks()
                    .get(tasklist=task_list_id or DEFAULT_TASK_LIST_ID, task=task_id)
                    .execute()
                ),
            )

            # Update fields
            if title is not None:
                task["title"] = title
            if notes is not None:
                task["notes"] = notes
            if completed is not None:
                task["status"] = "completed" if completed else "needsAction"
                if completed:
                    task["completed"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                else:
                    task.pop("completed", None)

            result = self._execute_with_backoff(
                "update_task",
                lambda: (
                    self.tasks_service.tasks()
                    .update(
                        tasklist=task_list_id or DEFAULT_TASK_LIST_ID,
                        task=task_id,
                        body=task,
                    )
                    .execute()
                ),
            )
            logger.info(f"Updated Google task: {task_id}")
            return result
        except HttpError as e:
            logger.error(f"Failed to update task: {e}")
            return None

    def delete_task(self, task_list_id: str, task_id: str) -> bool:
        """Delete a task from Google Tasks"""
        if not self.is_enabled():
            return False

        try:
            self._execute_with_backoff(
                "delete_task",
                lambda: (
                    self.tasks_service.tasks()
                    .delete(tasklist=task_list_id or DEFAULT_TASK_LIST_ID, task=task_id)
                    .execute()
                ),
            )
            logger.info(f"Deleted Google task: {task_id}")
            return True
        except HttpError as e:
            logger.error(f"Failed to delete task: {e}")
            return False

    def get_calendars(self) -> List[Dict[str, str]]:
        """Get all Google Calendars"""
        if not self.is_enabled():
            return []

        try:
            results = self.calendar_service.calendarList().list().execute()
            calendars = results.get("items", [])
            return [{"id": cal["id"], "summary": cal["summary"]} for cal in calendars]
        except HttpError as e:
            logger.error(f"Failed to get calendars: {e}")
            return []

    def create_calendar_event(
        self,
        calendar_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Create a calendar event"""
        if not self.is_enabled():
            return None

        try:
            event = {
                "summary": summary,
                "description": description,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                },
            }

            result = (
                self.calendar_service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
            logger.info(f"Created calendar event: {summary}")
            return result
        except HttpError as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None

    def fetch_remote_tasks(
        self, task_list_id: Optional[str] = None, include_completed: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch tasks from the primary or specified Google task list."""
        if not self.is_enabled():
            return []

        try:
            result = self._execute_with_backoff(
                "fetch_remote_tasks",
                lambda: (
                    self.tasks_service.tasks()
                    .list(
                        tasklist=task_list_id or DEFAULT_TASK_LIST_ID,
                        showCompleted=include_completed,
                        showHidden=False,
                        maxResults=100,
                    )
                    .execute()
                ),
            )
            return result.get("items", [])
        except HttpError as e:
            logger.error(f"Failed to fetch remote tasks: {e}")
            return []

    def sync_tasks_to_google(
        self, local_tasks: List[Dict[str, Any]], task_list_id: str
    ) -> bool:
        """Sync local tasks to Google Tasks"""
        if not self.is_enabled():
            return False

        try:
            # Get existing Google tasks
            google_tasks = self.get_tasks(task_list_id)
            google_task_map = {task.get("title"): task for task in google_tasks}

            # Sync each local task
            for local_task in local_tasks:
                title = local_task.get("title", "")
                if not title:
                    continue

                if title in google_task_map:
                    # Update existing task
                    google_task = google_task_map[title]
                    self.update_task(
                        task_list_id or DEFAULT_TASK_LIST_ID,
                        google_task["id"],
                        completed=local_task.get("completed", False),
                    )
                else:
                    # Create new task
                    self.create_task(
                        task_list_id or DEFAULT_TASK_LIST_ID,
                        title,
                        local_task.get("description", ""),
                    )

            logger.info(f"Synced {len(local_tasks)} tasks to Google Tasks")
            return True

        except Exception as e:
            logger.error(f"Failed to sync tasks: {e}")
            return False


def create_google_integration(config_dir: Path) -> GoogleIntegration:
    """Factory function to create Google integration instance"""
    return GoogleIntegration(config_dir)


if __name__ == "__main__":
    # Test the Google integration
    logging.basicConfig(level=logging.INFO)
    print("Testing Google Integration...")
    print("-" * 50)

    config_dir = Path.home() / ".ultimate-focus-timer"
    integration = create_google_integration(config_dir)

    if integration.is_enabled():
        print("✓ Google integration enabled")

        # Test task lists
        task_lists = integration.get_task_lists()
        print(f"\nFound {len(task_lists)} task lists:")
        for tl in task_lists:
            print(f"  - {tl['title']} (ID: {tl['id']})")

        # Test calendars
        calendars = integration.get_calendars()
        print(f"\nFound {len(calendars)} calendars:")
        for cal in calendars:
            print(f"  - {cal['summary']} (ID: {cal['id']})")
    else:
        print("✗ Google integration not available")
        print("\nTo enable:")
        print("1. Install dependencies: pip install google-auth google-auth-oauthlib google-api-python-client")
        print(f"2. Place credentials JSON at: {config_dir / 'google_credentials.json'}")
        print("3. Run authentication flow")
