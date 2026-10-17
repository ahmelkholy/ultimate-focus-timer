import subprocess
import sys
from unittest.mock import Mock

import pytest

from src.core import SessionState
from src.ui import FocusGUI


def test_unused_heavy_features_stay_unloaded(tmp_path):
    code = """
import sys
from pathlib import Path
import src.ui
from src.google_integration import GoogleIntegration
GoogleIntegration(Path(sys.argv[1]))
for name in ("googleapiclient.discovery", "google_auth_oauthlib.flow", "pystray", "PIL.Image", "matplotlib.pyplot", "pandas", "numpy", "sounddevice"):
    assert name not in sys.modules, name
"""
    subprocess.run([sys.executable, "-c", code, str(tmp_path)], check=True)


@pytest.mark.parametrize(
    "visible,timer,music,delay",
    [
        ("normal", SessionState.READY, "stopped", 60000),
        ("normal", SessionState.PAUSED, "paused", 60000),
        ("normal", SessionState.RUNNING, "stopped", 1000),
        ("normal", SessionState.READY, "playing", 1000),
        ("iconic", SessionState.READY, "playing", 60000),
    ],
)
def test_display_sleeps_when_idle_or_hidden(visible, timer, music, delay):
    gui = FocusGUI.__new__(FocusGUI)
    gui.root = Mock()
    gui.root.state.return_value = visible
    gui.session_manager = Mock(state=timer)
    gui.music = Mock(playback_state=music)
    gui.music_panel = Mock()
    gui.music_panel._actions.empty.return_value = True
    gui.mini_indicator = None
    gui.update_display = Mock()
    gui.schedule_callback = Mock(return_value="timer")
    gui.update_loop()
    gui.schedule_callback.assert_called_once_with(delay, gui.update_loop)
    if visible == "iconic":
        gui.update_display.assert_not_called()
