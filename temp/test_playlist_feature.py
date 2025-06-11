#!/usr/bin/env python3
"""
Test script to verify playlist selection functionality
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_playlist_functionality():
    """Test the playlist selection feature"""
    try:
        from config_manager import ConfigManager
        from music_controller import MusicController

        print("🎵 Testing Playlist Selection Feature")
        print("=" * 50)

        # Initialize components
        config = ConfigManager()
        music = MusicController(config)

        # Show current configuration
        playlist_dir = config.get("classical_music_playlist_dir", "Not configured")
        selected_playlist = config.get("classical_music_selected_playlist", "")

        print(f"📁 Playlist Directory: {playlist_dir}")
        print(f"🎯 Selected Playlist: {selected_playlist if selected_playlist else 'Auto (First Available)'}")

        # Get available playlists
        playlists = music.get_available_playlists()
        print(f"\n📋 Available Playlists: {len(playlists)}")

        if playlists:
            for i, playlist in enumerate(playlists, 1):
                marker = "➤" if playlist["path"] == selected_playlist else " "
                print(f"  {marker} {i}. {playlist['name']}")
                print(f"     📂 {playlist['path']}")
                print(f"     🏷️  Type: {playlist['type']}")
                print()
        else:
            print("  ❌ No playlists found!")
            return False

        # Test default selection
        default_playlist = music._select_default_playlist()
        if default_playlist:
            playlist_name = Path(default_playlist).stem
            print(f"▶️  Default Selection: {playlist_name}")
            print(f"   Path: {default_playlist}")
        else:
            print("❌ No default playlist selected")
            return False

        print("\n✅ Playlist selection feature working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing playlist functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_setting():
    """Test setting a specific playlist in config"""
    try:
        from config_manager import ConfigManager
        from music_controller import MusicController

        print("\n🔧 Testing Playlist Configuration")
        print("=" * 50)

        config = ConfigManager()
        music = MusicController(config)

        # Get available playlists
        playlists = music.get_available_playlists()
        if not playlists:
            print("❌ No playlists available for testing")
            return False

        # Test setting a specific playlist
        test_playlist = playlists[0]["path"]  # Use first available
        config.set("classical_music_selected_playlist", test_playlist)

        print(f"🔄 Set selected playlist to: {Path(test_playlist).name}")

        # Create new music controller to test
        music2 = MusicController(config)
        selected = music2._select_default_playlist()

        if selected == test_playlist:
            print("✅ Playlist selection works correctly!")

            # Reset to auto
            config.set("classical_music_selected_playlist", "")
            print("🔄 Reset to auto selection")
            return True
        else:
            print(f"❌ Expected {test_playlist}, got {selected}")
            return False

    except Exception as e:
        print(f"❌ Error testing config setting: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Focus Timer - Playlist Selection Test Suite")
    print("=" * 60)

    # Test 1: Basic functionality
    test1 = test_playlist_functionality()

    # Test 2: Configuration setting
    test2 = test_config_setting()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("🎉 ALL TESTS PASSED! Playlist selection feature is working!")
        print("\n💡 How to use:")
        print("1. Run the GUI: python main.py --gui")
        print("2. Click '⚙️ Settings'")
        print("3. Go to 'Music' tab")
        print("4. Select your preferred playlist from the dropdown")
        print("5. Click 'Save'")
        print("6. Start a session - your selected playlist will play!")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
