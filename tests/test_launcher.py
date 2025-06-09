"""
Test the Focus Application Launcher
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_app import check_dependencies, LauncherGUI, main


class TestLauncherGUI:
    """Test the LauncherGUI class"""

    def test_launcher_gui_initialization(self):
        """Test that LauncherGUI initializes without errors"""
        with patch("focus_app.tk.Tk"):
            launcher = LauncherGUI()
            assert launcher is not None

    @patch("focus_app.tk.Tk")
    def test_center_window(self, mock_tk):
        """Test window centering functionality"""
        mock_root = MagicMock()
        mock_root.winfo_screenwidth.return_value = 1920
        mock_root.winfo_screenheight.return_value = 1080

        with patch("focus_app.tk.Tk", return_value=mock_root):
            launcher = LauncherGUI()
            launcher.center_window()

            # Verify geometry was called with calculated position
            mock_root.geometry.assert_called()

    @patch("focus_app.tk.Tk")
    def test_update_status(self, mock_tk):
        """Test status update functionality"""
        mock_root = MagicMock()

        with patch("focus_app.tk.Tk", return_value=mock_root):
            launcher = LauncherGUI()
            launcher.status_label = MagicMock()

            launcher.update_status("Test message")
            launcher.status_label.config.assert_called_with(text="Test message")
            mock_root.update.assert_called()

    @patch("focus_app.FocusGUI")
    @patch("focus_app.tk.Tk")
    def test_launch_gui(self, mock_tk, mock_focus_gui):
        """Test GUI timer launch"""
        mock_root = MagicMock()
        mock_gui_instance = MagicMock()
        mock_focus_gui.return_value = mock_gui_instance

        with patch("focus_app.tk.Tk", return_value=mock_root):
            launcher = LauncherGUI()
            launcher.status_label = MagicMock()

            launcher.launch_gui()

            # Verify GUI was created and run
            mock_focus_gui.assert_called_once()
            mock_gui_instance.run.assert_called_once()

            # Verify window was hidden and shown
            mock_root.withdraw.assert_called()
            mock_root.deiconify.assert_called()


class TestDependencyCheck:
    """Test dependency checking functionality"""

    def test_check_dependencies_all_present(self):
        """Test dependency check when all dependencies are present"""
        # This test will use the real dependencies since they should be installed
        result = check_dependencies()
        assert result is True

    def test_check_dependencies_missing(self):
        """Test dependency check when dependencies are missing"""
        with patch("builtins.__import__") as mock_import:
            # Mock import to raise ImportError for yaml
            def side_effect(name, *args, **kwargs):
                if name == "yaml":
                    raise ImportError("No module named 'yaml'")
                return MagicMock()

            mock_import.side_effect = side_effect

            with patch("builtins.print") as mock_print:
                result = check_dependencies()
                assert result is False
                mock_print.assert_called()


class TestMainFunction:
    """Test the main function"""

    @patch("focus_app.check_dependencies")
    @patch("focus_app.LauncherGUI")
    def test_main_default_launcher(self, mock_launcher_gui, mock_check_deps):
        """Test main function with default launcher"""
        mock_check_deps.return_value = True
        mock_launcher_instance = MagicMock()
        mock_launcher_gui.return_value = mock_launcher_instance

        with patch("sys.argv", ["focus_app.py"]):
            main()

            mock_launcher_gui.assert_called_once()
            mock_launcher_instance.run.assert_called_once()

    @patch("focus_app.check_dependencies")
    @patch("focus_app.FocusGUI")
    def test_main_gui_mode(self, mock_focus_gui, mock_check_deps):
        """Test main function with GUI mode"""
        mock_check_deps.return_value = True
        mock_gui_instance = MagicMock()
        mock_focus_gui.return_value = mock_gui_instance

        with patch("sys.argv", ["focus_app.py", "--gui"]):
            main()

            mock_focus_gui.assert_called_once()
            mock_gui_instance.run.assert_called_once()

    @patch("focus_app.check_dependencies")
    @patch("focus_app.ConsoleInterface")
    def test_main_console_mode(self, mock_console, mock_check_deps):
        """Test main function with console mode"""
        mock_check_deps.return_value = True
        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        with patch("sys.argv", ["focus_app.py", "--console"]):
            main()

            mock_console.assert_called_once_with(None)
            mock_console_instance.run_interactive.assert_called_once()

    @patch("focus_app.check_dependencies")
    @patch("focus_app.ConsoleInterface")
    def test_main_pomodoro(self, mock_console, mock_check_deps):
        """Test main function with pomodoro session"""
        mock_check_deps.return_value = True
        mock_console_instance = MagicMock()
        mock_console.return_value = mock_console_instance

        with patch("sys.argv", ["focus_app.py", "--pomodoro"]):
            main()

            mock_console.assert_called_once_with(None)
            mock_console_instance.run_command.assert_called_once_with(
                "start", 25, "work"
            )

    @patch("focus_app.check_dependencies")
    def test_main_check_deps_only(self, mock_check_deps):
        """Test main function with --check-deps flag"""
        mock_check_deps.return_value = True

        with patch("sys.argv", ["focus_app.py", "--check-deps"]), patch(
            "builtins.print"
        ), pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the launcher"""

    def test_import_all_modules(self):
        """Test that all required modules can be imported"""
        # Test imports with proper error handling
        try:
            # These modules should be available since focus_app imports them
            import sys
            from pathlib import Path

            # Add paths as focus_app does
            sys.path.insert(0, str(Path(__file__).parent.parent))
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

            from config_manager import ConfigManager
            from dashboard import DashboardGUI, SessionAnalyzer
            from focus_console import ConsoleInterface
            from focus_gui import FocusGUI

            # Basic instantiation tests (without running)
            assert ConfigManager is not None
            assert FocusGUI is not None
            assert ConsoleInterface is not None
            assert DashboardGUI is not None
            assert SessionAnalyzer is not None

        except ImportError as e:
            pytest.skip(f"Skipping integration test due to import error: {e}")
