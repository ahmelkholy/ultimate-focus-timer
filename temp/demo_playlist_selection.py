#!/usr/bin/env python3
"""
Demo script showing the new playlist selection functionality
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our modules
from config_manager import ConfigManager
from music_controller import MusicController

def main():
    print("🎵 Focus Timer - Playlist Selection Demo")
    print("=" * 50)
    
    # Initialize components
    config = ConfigManager()
    music = MusicController(config)
    
    # Show playlist directory
    playlist_dir = config.get("classical_music_playlist_dir", "")
    print(f"📁 Playlist Directory: {playlist_dir}")
    
    # Show available playlists
    playlists = music.get_available_playlists()
    print(f"\n📋 Available Playlists ({len(playlists)}):")
    
    if not playlists:
        print("   ❌ No playlists found!")
        print(f"   💡 Make sure you have .m3u files in: {playlist_dir}")
        return
    
    for i, playlist in enumerate(playlists, 1):
        print(f"   {i}. 🎼 {playlist['name']}")
        print(f"      📂 {playlist['path']}")
        print(f"      🏷️  Type: {playlist['type']}")
        print()
    
    # Show current selection
    current_selected = config.get("classical_music_selected_playlist", "")
    print(f"🎯 Current Selection: {current_selected if current_selected else 'Auto (First Available)'}")
    
    # Show what would be played
    default_playlist = music._select_default_playlist()
    if default_playlist:
        playlist_name = Path(default_playlist).stem
        print(f"▶️  Would Play: {playlist_name}")
    else:
        print("❌ No playlist would be selected")
    
    print("\n✅ Playlist selection feature is working!")
    print("💡 Use the Settings dialog in the GUI to select a specific playlist.")

if __name__ == "__main__":
    main()
