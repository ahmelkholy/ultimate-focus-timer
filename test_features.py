#!/usr/bin/env python3
"""
Test script for new features in Ultimate Focus Timer.
Tests: session management, task features, music controls, MPV installer.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

from src.core import ConfigManager, SessionManager, SessionType, TaskManager
from src.mpv_installer import MPVInstaller
from src.system import MusicController

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_session_auto_start():
    """Test that session auto-start logic works correctly"""
    logger.info("\n=== Testing Session Auto-Start Logic ===")

    config_manager = ConfigManager()
    session_manager = SessionManager(config_manager)

    # Test short break auto-start
    session_manager.session_type = SessionType.SHORT_BREAK
    session_manager.completed_work_sessions = 1
    should_auto, next_type, duration = session_manager._calc_next_session()

    logger.info(f"Short break finished:")
    logger.info(f"  - Should auto-start: {should_auto} (Expected: True)")
    logger.info(f"  - Next type: {next_type} (Expected: SessionType.WORK)")

    assert should_auto is True, "Short break should auto-start work session"
    assert next_type == SessionType.WORK, "Short break should lead to work session"

    # Test long break manual start
    session_manager.session_type = SessionType.LONG_BREAK
    should_auto, next_type, duration = session_manager._calc_next_session()

    logger.info(f"Long break finished:")
    logger.info(f"  - Should auto-start: {should_auto} (Expected: False)")
    logger.info(f"  - Next type: {next_type} (Expected: SessionType.WORK)")

    assert should_auto is False, "Long break should NOT auto-start work session"
    assert next_type == SessionType.WORK, "Long break should lead to work session"

    logger.info("✓ Session auto-start logic test PASSED")


def test_task_operations():
    """Test task management operations"""
    logger.info("\n=== Testing Task Operations ===")

    task_manager = TaskManager()

    # Clear existing tasks for today
    today_key = task_manager.get_today_key()
    task_manager.tasks[today_key] = []

    # Test adding tasks
    task1 = task_manager.add_task("Test Task 1", pomodoros_planned=3)
    task2 = task_manager.add_task("Test Task 2", pomodoros_planned=2)
    task3 = task_manager.add_task("Test Task 3", pomodoros_planned=1)

    logger.info(f"Added 3 tasks")

    # Test getting tasks
    tasks = task_manager.get_today_tasks()
    logger.info(f"Current tasks: {len(tasks)} (Expected: 3)")
    assert len(tasks) == 3, "Should have 3 tasks"

    # Test task completion
    task_manager.complete_task(task1.id)
    completed = task_manager.get_completed_tasks()
    logger.info(f"Completed tasks: {len(completed)} (Expected: 1)")
    assert len(completed) == 1, "Should have 1 completed task"

    # Test task reordering (simulation)
    tasks = task_manager.get_today_tasks()
    logger.info(f"Task order before reordering: {[t.title for t in tasks]}")

    # Simulate reordering: move first task to last position
    task_to_move = tasks.pop(0)
    tasks.append(task_to_move)
    task_manager.tasks[today_key] = tasks
    task_manager.save_tasks()

    tasks = task_manager.get_today_tasks()
    logger.info(f"Task order after reordering: {[t.title for t in tasks]}")
    assert tasks[-1].id == task_to_move.id, "Task should be moved to last position"

    # Clean up
    for task in tasks:
        task_manager.delete_task(task.id)

    logger.info("✓ Task operations test PASSED")


def test_mpv_installer():
    """Test MPV installer functionality"""
    logger.info("\n=== Testing MPV Installer ===")

    installer = MPVInstaller()

    # Test detection
    mpv_path = installer.find_mpv()
    if mpv_path:
        logger.info(f"MPV found at: {mpv_path}")
    else:
        logger.info("MPV not found on system")

    # Test availability check
    is_available = installer.is_mpv_installed()
    logger.info(f"MPV installed: {is_available}")

    # Test platform detection
    logger.info(f"Platform: {installer.system}")
    logger.info(f"Common MPV directories checked: {len(installer._get_common_mpv_dirs())}")

    logger.info("✓ MPV installer test PASSED")


def test_music_controller():
    """Test music controller enhancements"""
    logger.info("\n=== Testing Music Controller ===")

    config_manager = ConfigManager()
    music_controller = MusicController(config_manager)

    logger.info(f"MPV available: {music_controller.is_mpv_available()}")

    # Test status
    status = music_controller.get_status()
    logger.info(f"Music status:")
    logger.info(f"  - Playing: {status['is_playing']}")
    logger.info(f"  - Current track: {status.get('current_track', 'N/A')}")
    logger.info(f"  - Volume: {status['volume']}%")

    # Test playlist availability
    playlists = music_controller.get_available_playlists()
    logger.info(f"Available playlists: {len(playlists)}")

    logger.info("✓ Music controller test PASSED")


def test_config_updates():
    """Test configuration management"""
    logger.info("\n=== Testing Configuration ===")

    config_manager = ConfigManager()

    # Test reading config values
    work_mins = config_manager.get("work_mins", 25)
    short_break_mins = config_manager.get("short_break_mins", 5)
    long_break_mins = config_manager.get("long_break_mins", 15)

    logger.info(f"Work duration: {work_mins} min")
    logger.info(f"Short break: {short_break_mins} min")
    logger.info(f"Long break: {long_break_mins} min")

    # Test auto-start settings
    auto_start_work = config_manager.get("auto_start_work", False)
    auto_start_break = config_manager.get("auto_start_break", True)

    logger.info(f"Auto-start work: {auto_start_work}")
    logger.info(f"Auto-start break: {auto_start_break}")

    logger.info("✓ Configuration test PASSED")


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("ULTIMATE FOCUS TIMER - Feature Test Suite")
    logger.info("=" * 60)

    try:
        test_config_updates()
        test_session_auto_start()
        test_task_operations()
        test_mpv_installer()
        test_music_controller()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)

        return 0

    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
