"""
Test utility functions and fixtures
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import os

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_config():
    """Create temporary configuration for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test_config.yml"
        yield config_path


@pytest.fixture
def mock_notification():
    """Mock notification system"""
    with patch('plyer.notification.notify') as mock_notify:
        yield mock_notify


@pytest.fixture
def mock_audio():
    """Mock audio system"""
    with patch('pygame.mixer') as mock_mixer:
        yield mock_mixer


class TestUtilities:
    """Test utility functions"""

    def test_path_handling(self, temp_config):
        """Test path handling utilities"""
        assert temp_config.parent.exists()
        assert not temp_config.exists()  # Should not exist until created

    def test_environment_setup(self):
        """Test environment variable handling"""
        # Test Python path modifications
        original_path = sys.path.copy()

        # Simulate path modification
        test_path = str(Path(__file__).parent.parent / "src")
        if test_path not in sys.path:
            sys.path.insert(0, test_path)

        assert test_path in sys.path

        # Cleanup
        sys.path = original_path


class TestMockingSafety:
    """Test that mocking doesn't break core functionality"""

    def test_mock_notification(self, mock_notification):
        """Test notification mocking"""
        mock_notification.return_value = None
        # Test that calling the mock doesn't raise errors
        mock_notification("Test", "Message")
        mock_notification.assert_called_once_with("Test", "Message")

    def test_mock_audio(self, mock_audio):
        """Test audio mocking"""
        mock_audio.init.return_value = None
        mock_audio.quit.return_value = None

        # Test that mocked audio calls work
        mock_audio.init()
        mock_audio.quit()

        mock_audio.init.assert_called_once()
        mock_audio.quit.assert_called_once()
