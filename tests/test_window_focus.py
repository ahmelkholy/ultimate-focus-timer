from types import SimpleNamespace
from unittest.mock import Mock

from src.core import SessionType
from src.ui import FocusGUI


def test_minimise_and_restore_only_wake_display():
    gui = FocusGUI.__new__(FocusGUI)
    gui.root = Mock()
    gui._wake_display = Mock()
    event = SimpleNamespace(widget=gui.root)
    gui.on_minimize(event)
    gui.on_restore(event)
    assert gui._wake_display.call_count == 2
    assert gui.root.mock_calls == []


def test_session_completion_does_not_activate_window():
    gui = FocusGUI.__new__(FocusGUI)
    gui.root = Mock()
    gui.config = Mock()
    gui.config.get.return_value = False
    gui._marshal = lambda callback: callback()
    for name in (
        "notifications",
        "tray",
        "music_panel",
        "music",
        "update_display",
        "update_button_states",
        "show_completion_dialog",
    ):
        setattr(gui, name, Mock())
    gui.on_session_complete(SessionType.WORK, 25)
    assert gui.root.mock_calls == []
    gui.notifications.show_session_complete.assert_called_once_with("work", 25)
