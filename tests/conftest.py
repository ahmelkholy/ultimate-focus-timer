"""
Shared test fixtures and configuration for the Ultimate Focus Timer test suite
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
import yaml


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for test configuration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        test_config = {
            'timer': {
                'work_duration': 25,
                'short_break_duration': 5,
                'long_break_duration': 15,
                'sessions_until_long_break': 4
            },
            'notifications': {
                'enabled': True,
                'sound': True,
                'desktop': True
            },
            'music': {
                'enabled': False,
                'volume': 0.5,
                'mpv_path': '/usr/bin/mpv'
            },
            'app': {
                'auto_start_breaks': False,
                'auto_start_work': False,
                'minimize_on_start': False,
                'data_path': str(Path(f.name).parent / 'test_data.json')
            }
        }
        yaml.dump(test_config, f)
        yield Path(f.name)

    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager for testing"""
    manager = MagicMock()
    manager.current_session = None
    manager.session_count = 0
    manager.is_running = False
    manager.is_paused = False
    manager.time_remaining = 0
    return manager


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager for testing"""
    manager = MagicMock()
    manager.config = {
        'timer': {
            'work_duration': 25,
            'short_break_duration': 5,
            'long_break_duration': 15,
            'sessions_until_long_break': 4
        },
        'notifications': {
            'enabled': True,
            'sound': True,
            'desktop': True
        },
        'music': {
            'enabled': False,
            'volume': 0.5,
            'mpv_path': '/usr/bin/mpv'
        },
        'app': {
            'auto_start_breaks': False,
            'auto_start_work': False,
            'minimize_on_start': False,
            'data_path': 'test_data.json'
        }
    }
    manager.get_timer_config.return_value = manager.config['timer']
    manager.get_app_config.return_value = manager.config['app']
    manager.get_notification_config.return_value = manager.config['notifications']
    manager.get_music_config.return_value = manager.config['music']
    return manager


@pytest.fixture
def mock_notification_manager():
    """Create a mock notification manager for testing"""
    manager = MagicMock()
    manager.show_notification = MagicMock()
    manager.play_sound = MagicMock()
    return manager


@pytest.fixture
def mock_music_controller():
    """Create a mock music controller for testing"""
    controller = MagicMock()
    controller.is_playing = False
    controller.play = MagicMock()
    controller.stop = MagicMock()
    controller.set_volume = MagicMock()
    return controller


@pytest.fixture
def sample_session_data():
    """Provide sample session data for testing"""
    return [
        {
            'start_time': '2024-01-01T10:00:00',
            'end_time': '2024-01-01T10:25:00',
            'duration': 25,
            'session_type': 'work',
            'completed': True,
            'interruptions': 0
        },
        {
            'start_time': '2024-01-01T10:30:00',
            'end_time': '2024-01-01T10:35:00',
            'duration': 5,
            'session_type': 'short_break',
            'completed': True,
            'interruptions': 0
        },
        {
            'start_time': '2024-01-01T11:00:00',
            'end_time': '2024-01-01T11:25:00',
            'duration': 25,
            'session_type': 'work',
            'completed': True,
            'interruptions': 1
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    # Set environment variables for testing
    os.environ['FOCUS_TIMER_TEST'] = '1'

    # Ensure we're in the correct directory
    test_dir = Path(__file__).parent
    project_dir = test_dir.parent
    os.chdir(project_dir)

    yield

    # Cleanup
    if 'FOCUS_TIMER_TEST' in os.environ:
        del os.environ['FOCUS_TIMER_TEST']


# Custom pytest markers
pytest_markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests",
    "gui: marks tests that require GUI components",
    "slow: marks tests as slow running",
]


def pytest_configure(config):
    """Configure pytest with custom markers"""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Auto-mark GUI tests
        if "gui" in item.nodeid.lower() or "tkinter" in str(item.function):
            item.add_marker(pytest.mark.gui)

        # Auto-mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
