#!/usr/bin/env python3
"""
google_integration.py - Google Tasks integration for Ultimate Focus Timer.

Connects the local task list with Google Tasks.
"""

import json
import logging
import pickle
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import Google API libraries
if TYPE_CHECKING:
    # Static-only imports for type checkers (Pylance / mypy).
    # Use underscore-prefixed aliases to avoid redefining runtime names (Flake8 F811).
    from google.oauth2.credentials import Credentials as _Credentials  # type: ignore
    from googleapiclient.errors import HttpError as _HttpError  # type: ignore

try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    GOOGLE_API_AVAILABLE = True
except ImportError:
    # Minimal runtime fallbacks. Keep only what's required at runtime.
    Request = None  # type: ignore[assignment]
    InstalledAppFlow = None  # type: ignore[assignment]
    build = None  # type: ignore[assignment]
    # Use Exception as a runtime fallback for HttpError so exception handlers work
    HttpError = Exception  # type: ignore[assignment]
    GOOGLE_API_AVAILABLE = False
    logger.warning("Google API libraries not installed. Google integration disabled.")


# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/tasks",
]

DEFAULT_TASK_LIST_ID = "@default"
GOOGLE_OAUTH_SETUP_URL = "https://console.cloud.google.com/apis/credentials/oauthclient"
GOOGLE_TASKS_API_OVERVIEW_URL = (
    "https://console.cloud.google.com/apis/library/tasks.googleapis.com"
)
GOOGLE_CONSOLE_URL_PATTERN = re.compile(r"https://console[^\s\"']+")


class GoogleIntegration:
    """Manages Google Tasks and Calendar integration"""

    def __init__(self, config_dir: Path):
        """Initialize Google integration"""
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.credentials_file = self.config_dir / "google_credentials.json"
        self.token_file = self.config_dir / "google_token.pickle"

        self.creds: Optional["_Credentials"] = None
        self.tasks_service = None
        self.calendar_service = None

        self.enabled = False
        self.last_error: Optional[str] = None
        self.last_error_help_url: Optional[str] = None

        if GOOGLE_API_AVAILABLE:
            self.reload()

    def _clear_session(self) -> None:
        """Reset the active Google session state."""
        self.creds = None
        self.tasks_service = None
        self.calendar_service = None
        self.enabled = False

    def has_credentials_file(self) -> bool:
        """Return True when the OAuth client secrets file is available."""
        return self.credentials_file.exists()

    def has_token(self) -> bool:
        """Return True when a saved OAuth token is available."""
        return self.token_file.exists()

    def _clear_last_error(self) -> None:
        """Clear the most recent API/setup error state."""
        self.last_error = None
        self.last_error_help_url = None

    def _set_last_error(self, message: str, help_url: Optional[str] = None) -> None:
        """Store the latest actionable Google integration error."""
        self.last_error = message
        self.last_error_help_url = help_url

    def _record_http_error(self, exc: "_HttpError") -> None:
        """Convert Google API HTTP failures into user-facing status."""
        raw_message = str(exc)
        help_url = None
        help_url_match = GOOGLE_CONSOLE_URL_PATTERN.search(raw_message)
        if help_url_match:
            help_url = help_url_match.group(0).rstrip('".,')

        if (
            "accessNotConfigured" in raw_message
            or "Google Tasks API has not been used" in raw_message
        ):
            self._set_last_error(
                "Google Tasks API is disabled for this Google Cloud project. "
                "Enable the Google Tasks API, wait a minute, then click Refresh Lists.",
                help_url or GOOGLE_TASKS_API_OVERVIEW_URL,
            )
            return

        self._set_last_error(raw_message, help_url)

    def get_connection_status(self) -> Dict[str, Any]:
        """Return the current Google Tasks connection state for UI/CLI callers."""
        return {
            "api_available": GOOGLE_API_AVAILABLE,
            "connected": self.enabled,
            "has_credentials_file": self.has_credentials_file(),
            "has_token": self.has_token(),
            "credentials_file": str(self.credentials_file),
            "token_file": str(self.token_file),
            "last_error": self.last_error,
            "last_error_help_url": self.last_error_help_url,
        }

    def install_credentials_file(self, source_path: Path) -> Path:
        """Copy a Google OAuth client secrets file into the app config directory."""
        resolved_source = Path(source_path).expanduser().resolve()
        if not resolved_source.exists():
            raise FileNotFoundError(
                f"Google credentials file not found: {resolved_source}"
            )

        with open(resolved_source, "r", encoding="utf-8-sig") as source_file:
            return self.install_credentials_content(source_file.read())

    def install_credentials_content(self, content: str) -> Path:
        """Validate and save a Google OAuth client JSON payload."""
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Google credentials content is not valid JSON.") from exc

        if not isinstance(parsed, dict) or not any(
            section in parsed for section in ("installed", "web")
        ):
            raise ValueError(
                "Google credentials JSON must contain an 'installed' or 'web' "
                "OAuth client section."
            )

        resolved_target = self.credentials_file.resolve()
        with open(resolved_target, "w", encoding="utf-8") as target_file:
            json.dump(parsed, target_file, indent=2, ensure_ascii=False)
            target_file.write("\n")
        logger.info("Saved Google credentials file to %s", resolved_target)
        return resolved_target

    def _save_token(self) -> None:
        """Persist the current OAuth token."""
        if not self.creds:
            raise RuntimeError("Cannot save an empty Google credential set")
        with open(self.token_file, "wb") as token:
            pickle.dump(self.creds, token)

    def _build_services(self) -> None:
        """Create Google Tasks service client."""
        if not self.creds:
            raise RuntimeError("Google credentials are not loaded")
        self.tasks_service = build(
            "tasks", "v1", credentials=self.creds, cache_discovery=False
        )
        self.calendar_service = None
        self.enabled = True

    def _load_credentials(
        self,
        allow_user_auth: bool = False,
        force_reauth: bool = False,
        raise_errors: bool = False,
    ) -> bool:
        """Load credentials silently or, when requested, complete browser auth."""
        self._clear_session()
        self._clear_last_error()
        try:
            if force_reauth and self.token_file.exists():
                self.token_file.unlink()

            # Load token if it exists
            if self.token_file.exists():
                try:
                    with open(self.token_file, "rb") as token:
                        self.creds = pickle.load(token)
                except Exception as exc:
                    logger.warning(
                        "Failed to read Google token from %s: %s", self.token_file, exc
                    )
                    self.creds = None

            if (
                self.creds
                and not self.creds.valid
                and self.creds.expired
                and self.creds.refresh_token
            ):
                logger.info("Refreshing Google credentials...")
                self.creds.refresh(Request())

            if not self.creds or not self.creds.valid:
                if not allow_user_auth:
                    logger.info("Google integration available but not connected yet")
                    return False
                if not self.credentials_file.exists():
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_file}"
                    )

                logger.info("Starting browser-based Google authentication...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES
                )
                self.creds = flow.run_local_server(
                    host="127.0.0.1",
                    port=0,
                    open_browser=True,
                    authorization_prompt_message=(
                        "Opening your browser to connect Google Tasks..."
                    ),
                    success_message=(
                        "Google Tasks is connected. You can close this window and "
                        "return to the app."
                    ),
                )

            if not self.creds or not self.creds.valid:
                logger.warning("Google credentials are not valid after loading")
                self._clear_session()
                return False

            self._save_token()
            self._build_services()
            self._clear_last_error()

            logger.info("Google integration enabled")
            return True

        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            self._set_last_error(str(e))
            self._clear_session()
            if raise_errors:
                raise
            return False

    def reload(self) -> bool:
        """Reload existing Google credentials without launching a browser."""
        if not GOOGLE_API_AVAILABLE:
            self._clear_session()
            return False
        return self._load_credentials(allow_user_auth=False)

    def connect(
        self,
        credentials_source: Optional[Path] = None,
        force_reauth: bool = False,
    ) -> bool:
        """Connect Google Tasks with an explicit browser-based OAuth flow."""
        if not GOOGLE_API_AVAILABLE:
            raise RuntimeError(
                "Google API libraries are not installed. Install requirements to "
                "enable Google Tasks."
            )
        if credentials_source is not None:
            self.install_credentials_file(credentials_source)
        return self._load_credentials(
            allow_user_auth=True, force_reauth=force_reauth, raise_errors=True
        )

    def disconnect(self) -> None:
        """Disconnect Google Tasks locally by removing the saved OAuth token."""
        if self.token_file.exists():
            self.token_file.unlink()
        self._clear_session()
        logger.info("Google integration disconnected")

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
                result = func()
                self._clear_last_error()
                return result
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
                self._record_http_error(exc)
                logger.error("%s failed: %s", action, exc)
                raise
            except Exception as exc:  # pragma: no cover - defensive
                self._set_last_error(str(exc))
                logger.error("%s failed unexpectedly: %s", action, exc)
                raise
        return None

    def get_task_lists(self) -> List[Dict[str, str]]:
        """Get all Google Tasks lists"""
        if not self.is_enabled():
            return []

        try:
            results = self._execute_with_backoff(
                "list_task_lists",
                lambda: self.tasks_service.tasklists().list().execute(),
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
        self,
        task_list_id: str,
        title: str,
        notes: str = "",
        due: Optional[datetime] = None,
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
                    task["completed"] = datetime.utcnow().strftime(
                        "%Y-%m-%dT%H:%M:%S.000Z"
                    )
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
        if not self.is_enabled() or self.calendar_service is None:
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
        if not self.is_enabled() or self.calendar_service is None:
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
    else:
        print("✗ Google integration not available")
        print("\nTo enable:")
        print(
            "1. Install dependencies: pip install google-auth "
            "google-auth-oauthlib google-api-python-client"
        )
        print(f"2. Place credentials JSON at: {config_dir / 'google_credentials.json'}")
        print(
            "3. Connect from Settings -> Tasks or run: "
            "focus --connect-tasks (or python main.py --connect-tasks)"
        )
