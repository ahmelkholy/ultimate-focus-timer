from unittest.mock import Mock

from src.core import ConfigManager
from src.ui import FocusGUI


def test_new_link_is_played_even_after_a_failure(tmp_path):
    gui = FocusGUI.__new__(FocusGUI)
    gui.config = ConfigManager(tmp_path / "config.yml")
    gui.music = Mock(is_playing=False, playback_state="error")
    gui.music_panel = Mock()
    gui.music_panel.run.side_effect = lambda action: action()
    gui.load_playlists = Mock()
    link = "https://www.youtube.com/watch?v=sJL3NuTkfRU"
    assert gui._save_music_link(link)
    gui.music.change_playlist.assert_called_once_with(link)
    assert gui.config.get("classical_music_selected_playlist") == link
    assert gui.music.last_error == ""


def test_invalid_link_leaves_preferences_and_player_unchanged(monkeypatch, tmp_path):
    gui = FocusGUI.__new__(FocusGUI)
    gui.config = ConfigManager(tmp_path / "config.yml")
    before = gui.config.config.copy()
    gui.root = Mock()
    gui.music = Mock()
    gui.music_panel = Mock()
    error = Mock()
    monkeypatch.setattr("src.ui.messagebox.showerror", error)
    assert not gui._save_music_link("https://youtu.be/first https://youtu.be/second")
    assert gui.config.config == before
    gui.music_panel.run.assert_not_called()
    error.assert_called_once()
