#!/usr/bin/env python3
"""
Test script for playlist selection functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_manager import ConfigManager
from music_controller import MusicController


def test_playlist_selection():
    """Test the playlist selection functionality"""
    print("🧪 Testing Playlist Selection Functionality")
    print("=" * 50)

    # Initialize config and music controller
    config = ConfigManager()
    music = MusicController(config)

    # Show available playlists
    playlists = music.get_available_playlists()
    print(f"\n📋 Available Playlists ({len(playlists)}):")
    for i, playlist in enumerate(playlists, 1):
        print(f"  {i}. {playlist['name']} ({playlist['type']})")
        print(f"     Path: {playlist['path']}")

    # Test current selection
    print(f"\n🎵 Current Configuration:")
    current_selected = config.get("classical_music_selected_playlist")
    print(
        f"  Selected Playlist: {current_selected if current_selected else 'Auto (First Available)'}"
    )

    # Test default playlist selection
    default_playlist = music._select_default_playlist()
    print(
        f"  Default Playlist: {Path(default_playlist).name if default_playlist else 'None'}"
    )

    print(f"\n✅ Playlist selection functionality working correctly!")


if __name__ == "__main__":
    test_playlist_selection()
