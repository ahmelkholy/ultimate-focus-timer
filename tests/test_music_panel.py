import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from unittest.mock import Mock

import pytest

from src.music_panel import MusicPanel
from src.ui import FocusGUI


@pytest.fixture
def root():
    try:
        window = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")
    window.withdraw()
    yield window
    window.destroy()


def test_panel_updates_controls_and_preserves_volume_drag(root):
    panel = MusicPanel(
        root, Mock(), Mock(get=lambda key, default: default), Mock(), Mock()
    )
    status = dict(
        state="playing",
        is_playing=True,
        error="",
        current_track="Now playing",
        current_playlist="https://youtube.com/watch?v=test",
        position=65,
        duration=180,
        volume=60,
        devices=[],
        route="Proxy",
    )
    panel.refresh(status)
    assert panel.title_label.cget("text") == "Now playing"
    assert panel.play_button.cget("text") == "Pause"
    assert panel.elapsed.cget("text") == "1:05"
    assert panel.duration_label.cget("text") == "3:00"
    panel._volume_drag = True
    panel.volume.set(30)
    panel.refresh({**status, "state": "paused"})
    assert panel.volume.get() == 30
    assert panel.play_button.cget("text") == "Resume"
    panel.destroy()


def test_zoom_restores_fonts_without_compounding(root):
    gui = FocusGUI.__new__(FocusGUI)
    gui.root = root
    gui.config = Mock()
    gui.main_frame = ttk.Frame(root)
    gui.music_panel = tk.Frame(root)
    gui.zoom_label = ttk.Label(root, text="100%")
    sample = tk.Label(root, text="Timer", font=("Arial", 20))
    gui._zoom_level = 1.0
    gui._zoom_fonts = {}
    gui.set_zoom(0.8, save=False, resize=False)
    assert tkfont.Font(root=root, font=sample.cget("font")).actual("size") == 16
    gui.set_zoom(1.0, save=False, resize=False)
    assert tkfont.Font(root=root, font=sample.cget("font")).actual("size") == 20
    gui.config.save_config.assert_not_called()


def test_replacement_request_is_not_dropped_while_an_action_runs(root):
    import threading

    panel = MusicPanel(
        root, Mock(), Mock(get=lambda key, default: default), Mock(), Mock()
    )
    started, release, replaced = threading.Event(), threading.Event(), threading.Event()

    def first():
        started.set()
        release.wait(3)

    panel.run(first)
    assert started.wait(2)
    panel.run(replaced.set)
    release.set()
    assert replaced.wait(2)
    panel.destroy()
