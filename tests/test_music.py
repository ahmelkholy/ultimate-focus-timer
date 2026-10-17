import io
from unittest.mock import Mock

from src.core import ConfigManager
from src.system import MusicController


def test_playlist_url_survives_config_round_trip(tmp_path):
    path = tmp_path / "config.yml"
    path.write_text(
        "classical_music_default_playlist: https://www.youtube.com/watch?v=abc&list=xyz\n"
    )
    config = ConfigManager(path)
    url = config.get("classical_music_default_playlist")
    assert url == "https://www.youtube.com/watch?v=abc&list=xyz"
    assert config.get_music_playlists()[0]["path"] == url
    assert not any("playlist not found" in issue for issue in config.validate_config())
    assert config.save_config()
    assert ConfigManager(path).get("classical_music_default_playlist") == url


def test_repairs_previously_collapsed_url_in_memory(tmp_path):
    path = tmp_path / "config.yml"
    original = "classical_music_default_playlist: https:/www.youtube.com/watch?v=abc\n"
    path.write_text(original)
    config = ConfigManager(path)
    assert config.get("classical_music_default_playlist").startswith("https://")
    assert path.read_text() == original


def controller(monkeypatch, tmp_path):
    monkeypatch.setattr(MusicController, "_find_mpv_executable", lambda self: "mpv")
    monkeypatch.setattr(MusicController, "_test_mpv_executable", lambda *args: True)
    return MusicController(ConfigManager(tmp_path / "config.yml"))


def test_player_exit_clears_false_playing_status(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    process = Mock(stdout=io.StringIO("network error\n"))
    process.wait.return_value = 2
    music.mpv_process = process
    music.is_playing = True
    music._monitor_playback(process)
    assert not music.is_playing
    assert music.get_status()["state"] == "error"
    assert music.get_status()["error"]


def test_old_player_cannot_change_new_player_status(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    old = Mock(stdout=io.StringIO("FOCUS_PLAYING:old track\n"))
    old.wait.return_value = 2
    music.mpv_process = Mock()
    music.is_playing = True
    music.playback_state = "loading"
    music._monitor_playback(old)
    assert music.is_playing
    assert music.playback_state == "loading"
    assert music.current_track_name == ""


def test_pause_and_volume_use_existing_player(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    music.mpv_process = Mock()
    music.mpv_process.poll.return_value = None
    music.is_playing = True
    music._send_mpv_command = Mock(return_value={"error": "success"})
    assert music.pause_music()
    assert music.playback_state == "paused"
    assert music.resume_music()
    assert music.set_volume(35)
    assert music._send_mpv_command.call_args.args[0] == ["set_property", "volume", 35]


def test_mac_proxy_running_uses_proxy(monkeypatch):
    import socket
    import urllib.request

    from src.system import _mac_music_proxy

    monkeypatch.setattr("src.system.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        urllib.request, "getproxies", lambda: {"http": "http://127.0.0.1:10808"}
    )
    from unittest.mock import MagicMock

    connection = MagicMock()
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: connection)
    assert _mac_music_proxy() == "http://127.0.0.1:10808"
    connection.__exit__.assert_called_once()


def test_mac_proxy_closed_uses_direct(monkeypatch):
    import socket
    import urllib.request

    from src.system import _mac_music_proxy

    monkeypatch.setattr("src.system.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        urllib.request, "getproxies", lambda: {"https": "http://localhost:10808"}
    )

    def refused(*args, **kwargs):
        raise ConnectionRefusedError()

    monkeypatch.setattr(socket, "create_connection", refused)
    assert _mac_music_proxy() == ""


def test_mac_without_proxy_uses_direct(monkeypatch):
    import urllib.request

    from src.system import _mac_music_proxy

    monkeypatch.setattr("src.system.platform.system", lambda: "Darwin")
    monkeypatch.setattr(urllib.request, "getproxies", dict)
    assert _mac_music_proxy() == ""


def test_gui_no_proxy_does_not_hide_mac_system_proxy(monkeypatch):
    import socket
    import urllib.request
    from unittest.mock import MagicMock

    from src.system import _mac_music_proxy

    monkeypatch.setattr("src.system.platform.system", lambda: "Darwin")
    monkeypatch.setattr(
        urllib.request, "getproxies", lambda: {"no": "localhost,127.0.0.1"}
    )
    monkeypatch.setattr(
        urllib.request,
        "getproxies_macosx_sysconf",
        lambda: {"http": "http://127.0.0.1:10808"},
        raising=False,
    )
    monkeypatch.setattr(socket, "create_connection", lambda *a, **kw: MagicMock())
    assert _mac_music_proxy() == "http://127.0.0.1:10808"


def test_live_player_events_keep_progress_pause_and_volume_in_sync(
    monkeypatch, tmp_path
):
    music = controller(monkeypatch, tmp_path)
    monkeypatch.setattr("src.system.time.monotonic", lambda: 100)
    music.is_playing = True
    music._apply_player_property("time-pos", 42)
    music._apply_player_property("duration", 180)
    music._apply_player_property("media-title", "A new track")
    music._apply_player_property("volume", 60)
    music._apply_player_property("pause", True)
    monkeypatch.setattr("src.system.time.monotonic", lambda: 110)
    status = music.get_status()
    assert status["position"] == 42
    assert status["duration"] == 180
    assert status["state"] == "paused"
    assert status["volume"] == 60
    assert status["current_track"] == "A new track"


def test_exact_double_paste_is_repaired_and_multiple_different_links_rejected():
    import pytest

    from src.system import normalise_music_link

    link = (
        "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU&start_radio=1"
    )
    assert normalise_music_link(link + link) == link
    with pytest.raises(ValueError):
        normalise_music_link(link + "https://youtu.be/another")
    with pytest.raises(ValueError):
        normalise_music_link("https://www.youtube.com/watch")


def test_retry_uses_new_selection_instead_of_failed_old_playlist(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    new = "https://www.youtube.com/watch?v=sJL3NuTkfRU"
    music.config.set("classical_music_default_playlist", new)
    music._paused_playlist = "https://www.youtube.com/playlist?list=removed"
    music.playback_state = "error"
    music.pid_file = tmp_path / "player.pid"
    process = Mock(pid=12345)
    launch = Mock(return_value=process)
    monkeypatch.setattr("src.system.subprocess.Popen", launch)
    monkeypatch.setattr("src.system.threading.Thread", Mock())
    assert music.start_music()
    assert launch.call_args.args[0][-1] == new


def test_unavailable_playlist_reports_specific_reason(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    process = Mock(
        stdout=io.StringIO(
            "WARNING: YouTube said: The playlist does not exist.\n"
            "[ytdl_hook] youtube-dl failed: unexpected error occurred\n"
        )
    )
    process.wait.return_value = 2
    music.mpv_process = process
    music.is_playing = True
    music._monitor_playback(process)
    assert "unavailable or private" in music.last_error


def test_youtube_radio_and_video_links_are_distinguished():
    from src.system import youtube_source_kind

    assert (
        youtube_source_kind(
            "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU&start_radio=1"
        )
        == "radio"
    )
    assert (
        youtube_source_kind("https://www.youtube.com/watch?v=sJL3NuTkfRU&list=PLtest")
        == "playlist"
    )
    assert youtube_source_kind("https://www.youtube.com/watch?v=sJL3NuTkfRU") == "video"
    assert youtube_source_kind("https://example.com/watch?list=RDtest") == ""


def test_radio_launch_expands_mix_without_unbounded_extraction(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    music.pid_file = tmp_path / "player.pid"
    launch = Mock(return_value=Mock(pid=12345))
    monkeypatch.setattr("src.system.subprocess.Popen", launch)
    monkeypatch.setattr("src.system.threading.Thread", Mock())
    url = "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU&start_radio=1"
    assert music.start_music(url)
    args = launch.call_args.args[0]
    assert "--ytdl-raw-options-append=yes-playlist=" in args
    assert "--ytdl-raw-options-append=playlist-end=50" in args
    assert args[-1] == url
    assert [arg for arg in args if arg.startswith("--shuffle=")][-1] == "--shuffle=no"


def test_radio_track_change_returns_from_loading_to_playing(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    music.playback_state = "playing"
    music.current_track_name = "Old song"
    music._live = {"time-pos": 180, "duration": 180, "pause": False}
    music._apply_player_event({"event": "start-file"})
    assert music.playback_state == "loading"
    assert not music.current_track_name
    assert music.get_status()["duration"] == 0
    music._apply_player_event(
        {"event": "property-change", "name": "media-title", "data": "Next song"}
    )
    music._apply_player_event({"event": "playback-restart"})
    assert music.playback_state == "playing"
    assert music.current_track_name == "Next song"


def test_chrome_session_is_opt_in_and_only_used_for_youtube(monkeypatch, tmp_path):
    from unittest.mock import Mock

    music = controller(monkeypatch, tmp_path)
    music.pid_file = tmp_path / "player.pid"
    launch = Mock(return_value=Mock(pid=12345))
    monkeypatch.setattr("src.system.subprocess.Popen", launch)
    monkeypatch.setattr("src.system.threading.Thread", Mock())
    youtube = "https://www.youtube.com/watch?v=sJL3NuTkfRU"
    flag = "--ytdl-raw-options-append=cookies-from-browser=chrome"
    assert music.start_music(youtube)
    assert flag not in launch.call_args.args[0]
    music.mpv_process = None
    music.config.set("youtube_browser", "chrome")
    assert music.start_music(youtube)
    assert flag in launch.call_args.args[0]
    music.mpv_process = None
    assert music.start_music("https://example.com/music.mp3")
    assert flag not in launch.call_args.args[0]


def test_finished_radio_refreshes_with_current_persisted_session(monkeypatch, tmp_path):
    music = controller(monkeypatch, tmp_path)
    source = "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU"
    music.current_playlist = source
    music.mpv_process = process = Mock()
    music.is_playing = True
    music._apply_player_property("playlist-count", 50)
    music._apply_player_property("playlist-pos", 49)
    # mpv clears these properties while exiting; retain the completed queue.
    music._apply_player_property("playlist-pos", None)
    music._apply_player_property("playlist-count", 0)
    music.start_music = Mock(return_value=True)
    assert music._refresh_completed_radio(process, 0)
    music.start_music.assert_called_once_with(source, _radio_continuation=True)


def test_radio_does_not_restart_after_stop_error_or_repeat_disabled(
    monkeypatch, tmp_path
):
    music = controller(monkeypatch, tmp_path)
    music.current_playlist = (
        "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU"
    )
    music.mpv_process = process = Mock()
    music._queue_count, music._queue_position = 50, 49
    music.start_music = Mock()
    music.is_playing = False
    assert not music._refresh_completed_radio(process, 0)
    music.is_playing = True
    assert not music._refresh_completed_radio(process, 2)
    music.config.set("classical_music_repeat", False)
    assert not music._refresh_completed_radio(process, 0)
    music.start_music.assert_not_called()


def test_radio_and_chrome_preferences_survive_reopen(tmp_path):
    path = tmp_path / "config.yml"
    first = ConfigManager(path)
    source = (
        "https://www.youtube.com/watch?v=sJL3NuTkfRU&list=RDsJL3NuTkfRU&start_radio=1"
    )
    for key, value in {
        "youtube_browser": "chrome",
        "classical_music_default_playlist": source,
        "classical_music_selected_playlist": source,
        "gui_zoom": 0.85,
        "radio_refresh": True,
    }.items():
        first.set(key, value)
    assert first.save_config()
    second = ConfigManager(path)
    assert second.get("youtube_browser") == "chrome"
    assert second.get("classical_music_selected_playlist") == source
    assert second.get("gui_zoom") == 0.85
    assert second.get("radio_refresh")
