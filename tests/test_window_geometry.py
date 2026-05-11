from src.ui import (
    _format_window_geometry,
    _normalise_window_geometry,
    _parse_window_geometry,
)


def test_parse_window_geometry_accepts_legacy_negative_offsets():
    assert _parse_window_geometry("250x720+-595+75") == (250, 720, -595, 75)


def test_normalise_window_geometry_formats_tk_compatible_offsets():
    assert _normalise_window_geometry("250x720+-595+-75") == "250x720-595-75"
    assert _normalise_window_geometry("900x700+40+80") == "900x700+40+80"


def test_parse_window_geometry_keeps_size_without_position():
    assert _parse_window_geometry("900x700") == (900, 700, None, None)
    assert _format_window_geometry(900, 700) == "900x700"


def test_parse_window_geometry_rejects_invalid_values():
    assert _parse_window_geometry("not-a-geometry") is None
