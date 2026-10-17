from types import SimpleNamespace
from unittest.mock import Mock

from src.core import SessionState, SessionType
from src.ui import FocusGUI


def gui_for_keys():
    gui = FocusGUI.__new__(FocusGUI)
    gui.root = Mock()
    gui.root.winfo_toplevel.return_value = gui.root
    gui.root.winfo_class.return_value = "Tk"
    gui.is_typing = Mock(return_value=False)
    gui._update_keyboard_mode = Mock()
    gui._last_d_press = 0
    gui.typing_active = False
    return gui


def key(gui, name, state=0):
    return gui._handle_app_key(
        SimpleNamespace(widget=gui.root, keysym=name, state=state)
    )


def test_vim_navigation_is_suppressed_during_text_entry():
    gui = gui_for_keys()
    gui.is_typing.return_value = True
    gui._vim_nav_down = Mock()
    gui.shortcut_delete_task = Mock()
    assert key(gui, "j") is None
    assert key(gui, "d") is None
    gui._vim_nav_down.assert_not_called()
    gui.shortcut_delete_task.assert_not_called()


def test_normal_mode_navigation_and_start_are_consumed_once():
    gui = gui_for_keys()
    gui._vim_nav_down = Mock()
    gui._keyboard_start_focus = Mock()
    assert key(gui, "j") == "break"
    assert key(gui, "Return") == "break"
    gui._vim_nav_down.assert_called_once()
    gui._keyboard_start_focus.assert_called_once()


def test_escape_leaves_input_without_dispatching_app_commands():
    gui = gui_for_keys()
    gui.typing_active = True
    gui.is_typing.return_value = True
    assert key(gui, "Escape") == "break"
    assert not gui.typing_active
    gui.root.focus_set.assert_called_once()


def test_modified_keys_do_not_run_single_key_commands():
    gui = gui_for_keys()
    gui._keyboard_start_focus = Mock()
    assert key(gui, "s", state=4) is None
    gui._keyboard_start_focus.assert_not_called()


def test_other_key_cancels_pending_double_delete():
    gui = gui_for_keys()
    gui._last_d_press = 100
    gui._vim_nav_down = Mock()
    key(gui, "j")
    assert gui._last_d_press == 0


def test_start_shortcut_does_not_replace_active_or_paused_session():
    gui = gui_for_keys()
    gui.session_manager = Mock(state=SessionState.RUNNING)
    gui.start_session = Mock()
    gui._keyboard_start_focus()
    gui.session_manager.state = SessionState.PAUSED
    gui._keyboard_start_focus()
    gui.start_session.assert_not_called()
    gui.session_manager.state = SessionState.READY
    gui._keyboard_start_focus()
    gui.start_session.assert_called_once_with(SessionType.WORK)


def test_focus_starts_on_selected_task():
    gui = gui_for_keys()
    first = SimpleNamespace(id="first", completed=False)
    selected = SimpleNamespace(id="selected", completed=False)
    gui.task_manager = Mock()
    gui.task_manager.get_today_tasks.return_value = [first, selected]
    gui.task_manager.get_incomplete_tasks.return_value = [first, selected]
    gui.selected_task_index = 1
    gui.session_manager = Mock()
    gui.update_button_states = Mock()
    gui.update_task_display = Mock()
    gui.start_session(SessionType.WORK)
    assert gui.current_task_id == "selected"
    gui.session_manager.start_session.assert_called_once_with(SessionType.WORK)


def test_double_delete_needs_a_selected_task():
    gui = gui_for_keys()
    gui.task_manager = Mock()
    gui.task_manager.get_today_tasks.return_value = [SimpleNamespace(id="keep")]
    gui.selected_task_index = -1
    gui._vim_delete_selected()
    gui.task_manager.delete_task.assert_not_called()


def test_entry_accept_and_cancel_stop_event_propagation():
    gui = gui_for_keys()
    gui.save_new_task = Mock()
    gui.cancel_add_task = Mock()
    assert gui._task_entry_accept() == "break"
    assert gui._task_entry_cancel() == "break"
    gui.save_new_task.assert_called_once()
    gui.cancel_add_task.assert_called_once()


def test_ttk_entries_are_recognized_as_input_fields():
    import tkinter as tk
    from tkinter import ttk

    import pytest

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")
    root.withdraw()
    try:
        gui = FocusGUI.__new__(FocusGUI)
        gui.root = Mock()
        for entry in (ttk.Entry(root), ttk.Spinbox(root), ttk.Combobox(root)):
            gui.root.focus_get.return_value = entry
            assert gui.is_typing()
    finally:
        root.destroy()
