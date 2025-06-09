#!/usr/bin/env python3
"""Test script for pause/resume functionality"""

import sys
import time
sys.path.append('src')

from session_manager import SessionManager, SessionType
from config_manager import ConfigManager
from music_controller import MusicController
from notification_manager import NotificationManager

def test_pause_resume():
    print('🧪 Testing pause/resume functionality...')

    # Initialize components
    config = ConfigManager()
    music = MusicController(config)
    notifications = NotificationManager(config)
    session_manager = SessionManager(config, music, notifications)

    # Start a work session (10 seconds)
    print('🎯 Starting 10-second work session...')
    session_manager.start_session(SessionType.WORK, 10/60)  # 10 seconds

    # Let it run for a few seconds
    time.sleep(3)
    info = session_manager.get_session_info()
    print(f'📊 Status after 3s: {info["state"]} | Elapsed: {info["elapsed_seconds"]}s')

    # Test pause
    print('⏸️  Testing pause...')
    success = session_manager.pause_session()
    print(f'Pause result: {success}')

    info = session_manager.get_session_info()
    print(f'📊 Status after pause: {info["state"]} | Elapsed: {info["elapsed_seconds"]}s')

    # Wait while paused
    time.sleep(2)

    info = session_manager.get_session_info()
    print(f'📊 Status after 2s pause: {info["state"]} | Elapsed: {info["elapsed_seconds"]}s')

    # Test resume
    print('▶️  Testing resume...')
    success = session_manager.resume_session()
    print(f'Resume result: {success}')

    info = session_manager.get_session_info()
    print(f'📊 Status after resume: {info["state"]} | Elapsed: {info["elapsed_seconds"]}s')

    # Let it run until completion
    time.sleep(8)

    final_info = session_manager.get_session_info()
    print(f'🏁 Final status: {final_info["state"]} - {final_info["type"]}')

    # Cleanup
    session_manager.cleanup()
    print('✨ Pause/Resume test completed!')

if __name__ == "__main__":
    test_pause_resume()
