#!/usr/bin/env python3
"""
Cross-Platform Notification Manager for Enhanced Focus Timer
Handles desktop notifications across Windows, macOS, and Linux
"""

import platform
from typing import Optional

try:
    from plyer import notification

    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    notification = None
    print("plyer not available - install with: pip install plyer")

# Platform-specific imports
if platform.system() == "Darwin":  # macOS
    try:
        import pync

        PYNC_AVAILABLE = True
    except ImportError:
        PYNC_AVAILABLE = False


class NotificationManager:
    """Cross-platform notification manager"""

    def __init__(self, config_manager):
        """Initialize notification manager with configuration"""
        self.config = config_manager

        # Check if notifications are enabled
        self.notifications_enabled = self.config.get("desktop_notifications", True)

        # Determine best notification method for platform
        self.notification_method = self._get_best_notification_method()

    def _get_best_notification_method(self) -> str:
        """Determine the best notification method for current platform"""
        system = platform.system()

        if not self.notifications_enabled:
            return "disabled"

        if system == "Windows":
            if PLYER_AVAILABLE:
                return "plyer"
            else:
                return "console"

        elif system == "Darwin":  # macOS
            if PYNC_AVAILABLE:
                return "pync"
            elif PLYER_AVAILABLE:
                return "plyer"
            else:
                return "osascript"

        elif system == "Linux":
            if PLYER_AVAILABLE:
                return "plyer"
            else:
                return "notify-send"

        else:
            return "console"

    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        duration: Optional[int] = None,
    ) -> bool:
        """
        Show desktop notification

        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification ('info', 'success', 'warning', 'error')
            duration: Duration in seconds (None for default)

        Returns:
            True if notification was shown successfully
        """
        if not self.notifications_enabled:
            return False

        if duration is None:
            duration = self.config.get("notification_persistence", 5)

        try:
            if self.notification_method == "disabled":
                return False

            elif self.notification_method == "pync":
                return self._show_pync(title, message, duration)

            elif self.notification_method == "plyer":
                return self._show_plyer(title, message, duration)

            elif self.notification_method == "osascript":
                return self._show_osascript(title, message)

            elif self.notification_method == "notify-send":
                return self._show_notify_send(title, message, duration)

            else:  # console fallback
                return self._show_console(title, message, notification_type)

        except Exception as e:
            print(f"Notification error: {e}")
            # Fallback to console
            return self._show_console(title, message, notification_type)

    def _show_pync(self, title: str, message: str, duration: int) -> bool:
        """Show notification using pync (macOS)"""
        try:
            pync.notify(message, title=title, timeout=duration)
            return True
        except Exception as e:
            print(f"pync error: {e}")
            return False

    def _show_plyer(self, title: str, message: str, duration: int) -> bool:
        """Show notification using plyer (cross-platform)"""
        try:
            if notification is None:
                print("plyer not available")
                return False
            notification.notify(title=title, message=message, timeout=duration)
            return True
        except Exception as e:
            print(f"plyer error: {e}")
            return False

    def _show_osascript(self, title: str, message: str) -> bool:
        """Show notification using osascript (macOS fallback)"""
        try:
            import subprocess

            script = f"""
            display notification "{message}" with title "{title}"
            """

            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True
        except Exception as e:
            print(f"osascript error: {e}")
            return False

    def _show_notify_send(self, title: str, message: str, duration: int) -> bool:
        """Show notification using notify-send (Linux)"""
        try:
            import subprocess

            subprocess.run(
                [
                    "notify-send",
                    "-t",
                    str(duration * 1000),  # notify-send uses milliseconds
                    title,
                    message,
                ],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception as e:
            print(f"notify-send error: {e}")
            return False

    def _show_console(self, title: str, message: str, notification_type: str) -> bool:
        """Show notification in console (fallback)"""
        # Color coding for different notification types
        colors = {
            "info": "\033[94m",  # Blue
            "success": "\033[92m",  # Green
            "warning": "\033[93m",  # Yellow
            "error": "\033[91m",  # Red
        }

        reset_color = "\033[0m"
        color = colors.get(notification_type, colors["info"])

        print(f"\n{color} {title}{reset_color}")
        print(f"{color} {message}{reset_color}\n")

        return True

    def show_session_start(self, session_type: str, duration: int) -> bool:
        """Show notification for session start"""
        icons = {"work": "🎯", "short_break": "☕", "long_break": "🛋️", "custom": "⏱️"}
        icon = icons.get(session_type, "⏱️")
        title = f"{icon} Focus Session Started"
        message = f"{session_type.replace('_', ' ').title()} session ({duration} min)"

        return self.show_notification(title, message, "info")

    def show_session_complete(self, session_type: str, duration: int) -> bool:
        """Show notification for session completion"""
        title = "🎉 Session Complete!"
        message = f"Great work! You completed a {duration}-minute {session_type.replace('_', ' ')} session."

        return self.show_notification(title, message, "success")

    def show_early_warning(self, session_type: str, minutes_remaining: int) -> bool:
        """Show early warning notification"""
        title = "⏰ Time Warning"
        message = f"{minutes_remaining} minute(s) remaining in your {session_type.replace('_', ' ')} session"

        return self.show_notification(title, message, "warning")

    def show_motivational_message(self, message: str) -> bool:
        """Show motivational message"""
        if not self.config.get("motivational_messages", True):
            return False

        title = "💪 Stay Focused!"
        return self.show_notification(title, message, "info")

    def test_notifications(self) -> bool:
        """Test notification system"""
        print("🧪 Testing notification system...")

        print(f"Platform: {platform.system()}")
        print(f"Method: {self.notification_method}")

        # Test basic notification
        success = self.show_notification(
            "🧪 Test Notification",
            "If you can see this, notifications are working!",
            "info",
        )

        if success:
            print("✅ Notification test successful")
        else:
            print("❌ Notification test failed")

        return success

    def enable_notifications(self) -> None:
        """Enable notifications"""
        self.notifications_enabled = True
        self.config.set("desktop_notifications", True)
        print("✅ Notifications enabled")

    def disable_notifications(self) -> None:
        """Disable notifications"""
        self.notifications_enabled = False
        self.config.set("desktop_notifications", False)
        print("🔇 Notifications disabled")


# Motivational messages for different scenarios
MOTIVATIONAL_MESSAGES = {
    "work_start": [
        "Time to focus and make progress!",
        "You've got this! Let's get to work.",
        "Deep focus mode activated!",
        "Every minute counts. Let's do this!",
        "Focus on the task at hand.",
    ],
    "work_complete": [
        "Excellent work! You're building great habits.",
        "Another successful focus session! Keep it up!",
        "Well done! Your productivity is improving.",
        "Great job staying focused!",
        "You're on fire! Keep the momentum going.",
    ],
    "break_start": [
        "Time to recharge and refresh!",
        "Take a well-deserved break.",
        "Rest your mind for a moment.",
        "You've earned this break!",
        "Relax and come back stronger.",
    ],
    "daily_goal": [
        "You're making great progress today!",
        "Keep up the excellent work!",
        "Your focus is paying off!",
        "Productivity level: Outstanding!",
        "You're in the zone today!",
    ],
}


if __name__ == "__main__":
    # Test notification manager
    from config_manager import ConfigManager

    config = ConfigManager()
    notifications = NotificationManager(config)

    # Test basic functionality
    notifications.test_notifications()

    # Test different notification types
    test_notifications = (
        input("\nTest different notification types? (y/n): ").lower().strip()
    )
    if test_notifications == "y":
        import time

        notifications.show_session_start("work", 25)

        notifications.show_early_warning("work", 2)
        time.sleep(2)

        notifications.show_session_complete("work", 25)
        time.sleep(2)

        notifications.show_motivational_message("You're doing great!")
