#!/usr/bin/env python3
"""Test script for auto-start break functionality"""

import sys
import time
sys.path.append('src')

from session_manager import SessionManager, SessionType
from config_manager import ConfigManager
from music_controller import MusicController
from notification_manager import NotificationManager

def test_auto_start():
    print('🧪 Testing auto-start break functionality...')

    # Initialize components
    config = ConfigManager()
    music = MusicController(config)
    notifications = NotificationManager(config)
    session_manager = SessionManager(config, music, notifications)

    def on_complete(session_type, duration):
        print(f'✅ Completion callback: {session_type.value} session ({duration} min)')

    # Set up callback
    session_manager.set_callbacks(on_complete=on_complete)

    # Start a very short work session (3 seconds)
    print('🎯 Starting 3-second work session...')
    session_manager.start_session(SessionType.WORK, 0.05)  # 0.05 minutes = 3 seconds

    # Monitor session progress
    start_time = time.time()
    while time.time() - start_time < 10:  # Monitor for up to 10 seconds
        info = session_manager.get_session_info()
        print(f'📊 Status: {info["state"]} | Type: {info["type"]} | Elapsed: {info["elapsed_seconds"]}s')
        time.sleep(1)

        # Check if we've moved to a break session
        if info["type"] in ["short_break", "long_break"]:
            print(f'🎉 SUCCESS! Auto-started {info["type"]} session!')
            break

    # Final status
    final_info = session_manager.get_session_info()
    print(f'🏁 Final status: {final_info["state"]} - {final_info["type"]}')

    # Cleanup
    session_manager.cleanup()
    print('✨ Test completed!')

if __name__ == "__main__":
    test_auto_start()
