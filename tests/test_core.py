"""
Test configuration and session management functionality
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from session_manager import SessionManager


class TestConfigManager:
    """Test configuration management"""

    def test_config_creation(self):
        """Test configuration file creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)
            assert config_path.exists()

    def test_config_defaults(self):
        """Test default configuration values"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)

            # Test essential default values
            assert config.get("timer.work_duration") == 25
            assert config.get("timer.short_break") == 5
            assert config.get("timer.long_break") == 15
            assert config.get("app.theme") == "dark"

    def test_config_update(self):
        """Test configuration updates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)

            # Update a value
            config.update("timer.work_duration", 30)
            assert config.get("timer.work_duration") == 30

            # Verify persistence
            config2 = ConfigManager(config_path)
            assert config2.get("timer.work_duration") == 30

    def test_config_validation(self):
        """Test configuration validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)

            # Test invalid values
            with pytest.raises((ValueError, TypeError)):
                config.update("timer.work_duration", -5)

    def test_config_backup(self):
        """Test configuration backup functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)

            # Create backup
            backup_path = config.create_backup()
            assert backup_path.exists()
            assert "backup" in str(backup_path)


class TestSessionManager:
    """Test session management"""

    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yml"
            config = ConfigManager(config_path)
            yield SessionManager(config)

    def test_session_creation(self, session_manager):
        """Test session creation"""
        session = session_manager.create_session("work", 25)
        assert session["type"] == "work"
        assert session["duration"] == 25
        assert "start_time" in session
        assert "session_id" in session

    def test_session_timing(self, session_manager):
        """Test session timing functionality"""
        session = session_manager.create_session("work", 1)  # 1 minute for testing

        # Start session
        session_manager.start_session(session["session_id"])
        assert session_manager.is_active()

        # Check remaining time
        remaining = session_manager.get_remaining_time()
        assert 0 < remaining <= 60

    def test_session_pause_resume(self, session_manager):
        """Test session pause and resume"""
        session = session_manager.create_session("work", 25)
        session_id = session["session_id"]

        session_manager.start_session(session_id)
        assert session_manager.is_active()

        # Pause session
        session_manager.pause_session()
        assert session_manager.is_paused()

        # Resume session
        session_manager.resume_session()
        assert session_manager.is_active()
        assert not session_manager.is_paused()

    def test_session_statistics(self, session_manager):
        """Test session statistics tracking"""
        # Create and complete a session
        session = session_manager.create_session("work", 0.1)  # Very short for testing
        session_id = session["session_id"]

        session_manager.start_session(session_id)
        session_manager.complete_session()

        # Check statistics
        stats = session_manager.get_statistics()
        assert "total_sessions" in stats
        assert "total_time" in stats
        assert stats["total_sessions"] >= 1

    def test_session_data_persistence(self, session_manager):
        """Test session data persistence"""
        # Create session
        session = session_manager.create_session("work", 25)
        session_id = session["session_id"]

        # Save session data
        session_manager.save_session_data()

        # Verify data can be loaded
        loaded_data = session_manager.load_session_data()
        assert len(loaded_data) > 0


class TestModuleImports:
    """Test that all modules can be imported correctly"""

    def test_import_config_manager(self):
        """Test config manager import"""
        from config_manager import ConfigManager

        assert ConfigManager is not None

    def test_import_session_manager(self):
        """Test session manager import"""
        from session_manager import SessionManager

        assert SessionManager is not None

    def test_import_music_controller(self):
        """Test music controller import"""
        try:
            from music_controller import MusicController

            assert MusicController is not None
        except ImportError:
            pytest.skip("Music controller dependencies not available")

    def test_import_notification_manager(self):
        """Test notification manager import"""
        try:
            from notification_manager import NotificationManager

            assert NotificationManager is not None
        except ImportError:
            pytest.skip("Notification manager dependencies not available")

    def test_import_gui_components(self):
        """Test GUI component imports"""
        try:
            from focus_gui import FocusGUI

            assert FocusGUI is not None
        except ImportError:
            pytest.skip("GUI dependencies not available")

    def test_import_console_components(self):
        """Test console component imports"""
        try:
            from focus_console import FocusConsole

            assert FocusConsole is not None
        except ImportError:
            pytest.skip("Console dependencies not available")

    def test_import_dashboard(self):
        """Test dashboard import"""
        try:
            from dashboard import Dashboard

            assert Dashboard is not None
        except ImportError:
            pytest.skip("Dashboard dependencies not available")

    def test_import_cli(self):
        """Test CLI import"""
        try:
            from cli import CLI

            assert CLI is not None
        except ImportError:
            pytest.skip("CLI dependencies not available")


class TestApplicationIntegration:
    """Test application integration"""

    @patch("sys.argv", ["main.py", "--help"])
    def test_main_help(self):
        """Test main application help"""
        try:
            import main

            # Should not raise exception when importing
            assert main is not None
        except SystemExit:
            # Help command exits, this is expected
            pass

    @patch("sys.argv", ["focus_app.py", "--help"])
    def test_focus_app_help(self):
        """Test focus app help"""
        try:
            import focus_app

            assert focus_app is not None
        except SystemExit:
            # Help command exits, this is expected
            pass


class TestVersionInfo:
    """Test version information"""

    def test_version_import(self):
        """Test version information import"""
        try:
            from __version__ import __version__, get_version

            assert __version__ is not None
            assert get_version() == __version__
        except ImportError:
            pytest.skip("Version information not available")

    def test_package_init(self):
        """Test package initialization"""
        try:
            import src

            assert hasattr(src, "__version__")
        except (ImportError, AttributeError):
            pytest.skip("Package initialization not complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
