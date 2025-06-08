#!/usr/bin/env python3
"""
Focus Timer Setup Script
Automated setup and configuration for the Focus Timer application
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


class SetupManager:
    """Manages the setup process for Focus Timer"""

    def __init__(self):
        self.system = platform.system()
        self.app_dir = Path(__file__).parent
        self.python_exe = sys.executable
        self.errors = []
        self.warnings = []

    def print_header(self):
        """Print setup header"""
        print("═" * 70)
        print("                  🎯 FOCUS TIMER SETUP")
        print("                 Python Cross-Platform")
        print("═" * 70)
        print()
        print(f"🖥️  System: {self.system} {platform.release()}")
        print(f"🐍 Python: {sys.version}")
        print(f"📁 App Directory: {self.app_dir}")
        print()

    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        print("🔍 Checking Python version...")

        if sys.version_info < (3, 7):
            self.errors.append("Python 3.7+ is required")
            print("❌ Python 3.7+ is required")
            return False

        print(
            f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        return True

    def check_pip(self) -> bool:
        """Check if pip is available"""
        print("🔍 Checking pip...")

        try:
            import pip

            print("✅ pip is available")
            return True
        except ImportError:
            try:
                subprocess.check_call(
                    [self.python_exe, "-m", "pip", "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print("✅ pip is available")
                return True
            except subprocess.CalledProcessError:
                self.errors.append("pip is not available")
                print("❌ pip is not available")
                return False

    def install_dependencies(self) -> bool:
        """Install required Python dependencies"""
        print("📦 Installing dependencies...")

        requirements_file = self.app_dir / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found")
            self.errors.append("requirements.txt file missing")
            return False

        try:
            # Upgrade pip first
            print("   Upgrading pip...")
            subprocess.check_call(
                [self.python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Install requirements
            print("   Installing packages...")
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                self.errors.append(f"Dependency installation failed: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            self.errors.append(f"Dependency installation failed: {e}")
            return False

    def check_mpv(self) -> bool:
        """Check if MPV player is available"""
        print("🎵 Checking MPV player...")

        mpv_commands = ["mpv", "mpv.exe"]
        if self.system == "Windows":
            mpv_commands.extend(
                [
                    str(Path.home() / "mpv" / "mpv.exe"),
                    "C:\\Program Files\\mpv\\mpv.exe",
                    "C:\\Program Files (x86)\\mpv\\mpv.exe",
                ]
            )

        for cmd in mpv_commands:
            try:
                subprocess.check_call(
                    [cmd, "--version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"✅ MPV found: {cmd}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        print("⚠️  MPV player not found")
        self.warnings.append("MPV player not found - music features will be disabled")
        return False

    def setup_directories(self) -> bool:
        """Create necessary directories"""
        print("📁 Setting up directories...")

        directories = [
            self.app_dir / "log",
            self.app_dir / "exports",
            self.app_dir / "music",
            Path.home() / ".focus-timer",
        ]

        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {directory}")

            print("✅ Directories created successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to create directories: {e}")
            self.errors.append(f"Directory creation failed: {e}")
            return False

    def create_default_config(self) -> bool:
        """Create default configuration if it doesn't exist"""
        print("⚙️  Setting up configuration...")

        config_file = self.app_dir / "config.yml"

        if config_file.exists():
            print("✅ Configuration file already exists")
            return True

        try:
            # Import config manager to create default config
            sys.path.insert(0, str(self.app_dir))
            from config_manager import ConfigManager

            config = ConfigManager()
            print("✅ Default configuration created")
            return True

        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            self.errors.append(f"Configuration creation failed: {e}")
            return False

    def setup_shortcuts(self) -> bool:
        """Create desktop shortcuts and start menu entries"""
        print("🔗 Setting up shortcuts...")

        try:
            if self.system == "Windows":
                self._setup_windows_shortcuts()
            elif self.system == "Darwin":
                self._setup_macos_shortcuts()
            elif self.system == "Linux":
                self._setup_linux_shortcuts()

            print("✅ Shortcuts created successfully")
            return True

        except Exception as e:
            print(f"⚠️  Could not create shortcuts: {e}")
            self.warnings.append(f"Shortcut creation failed: {e}")
            return False

    def _setup_windows_shortcuts(self):
        """Setup Windows shortcuts"""
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()
        start_menu = winshell.start_menu()

        # Desktop shortcut
        desktop_link = Path(desktop) / "Focus Timer.lnk"
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(desktop_link))
        shortcut.Targetpath = self.python_exe
        shortcut.Arguments = f'"{self.app_dir / "focus_app.py"}"'
        shortcut.WorkingDirectory = str(self.app_dir)
        shortcut.IconLocation = f"{self.app_dir / 'focus_app.py'},0"
        shortcut.save()

        # Start menu shortcut
        programs_dir = Path(start_menu) / "Programs" / "Focus Timer"
        programs_dir.mkdir(parents=True, exist_ok=True)

        start_link = programs_dir / "Focus Timer.lnk"
        shortcut = shell.CreateShortCut(str(start_link))
        shortcut.Targetpath = self.python_exe
        shortcut.Arguments = f'"{self.app_dir / "focus_app.py"}"'
        shortcut.WorkingDirectory = str(self.app_dir)
        shortcut.save()

    def _setup_macos_shortcuts(self):
        """Setup macOS shortcuts"""
        # Create .app bundle
        app_dir = Path.home() / "Applications" / "Focus Timer.app"
        contents_dir = app_dir / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"

        app_dir.mkdir(parents=True, exist_ok=True)
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)

        # Info.plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>focus_timer</string>
    <key>CFBundleIdentifier</key>
    <string>com.focus-timer.app</string>
    <key>CFBundleName</key>
    <string>Focus Timer</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
</dict>
</plist>"""

        with open(contents_dir / "Info.plist", "w") as f:
            f.write(plist_content)

        # Executable script
        script_content = f"""#!/bin/bash
cd "{self.app_dir}"
"{self.python_exe}" focus_app.py
"""

        script_file = macos_dir / "focus_timer"
        with open(script_file, "w") as f:
            f.write(script_content)

        script_file.chmod(0o755)

    def _setup_linux_shortcuts(self):
        """Setup Linux shortcuts"""
        # Desktop entry
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Timer
Comment=Productivity timer using the Pomodoro Technique
Exec={self.python_exe} {self.app_dir / "focus_app.py"}
Icon={self.app_dir / "focus_app.py"}
Terminal=false
Categories=Office;Productivity;
"""

        # User applications directory
        apps_dir = Path.home() / ".local" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)

        with open(apps_dir / "focus-timer.desktop", "w") as f:
            f.write(desktop_entry)

        # Desktop shortcut
        desktop_dir = Path.home() / "Desktop"
        if desktop_dir.exists():
            desktop_file = desktop_dir / "focus-timer.desktop"
            with open(desktop_file, "w") as f:
                f.write(desktop_entry)
            desktop_file.chmod(0o755)

    def verify_installation(self) -> bool:
        """Verify that the installation is working"""
        print("🧪 Verifying installation...")

        try:
            # Test imports
            sys.path.insert(0, str(self.app_dir))

            print("   Testing imports...")
            from config_manager import ConfigManager
            from music_controller import MusicController
            from notification_manager import NotificationManager
            from session_manager import SessionManager

            print("   ✅ Core modules imported successfully")

            # Test configuration
            print("   Testing configuration...")
            config = ConfigManager()
            timer_config = config.get_timer_config()
            print("   ✅ Configuration loaded successfully")

            # Test session manager
            print("   Testing session manager...")
            session_manager = SessionManager(config)
            status = session_manager.get_status()
            print("   ✅ Session manager working")

            print("✅ Installation verified successfully")
            return True

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            self.errors.append(f"Installation verification failed: {e}")
            return False

    def install_optional_packages(self):
        """Install optional packages for enhanced functionality"""
        print("📦 Installing optional packages...")

        optional_packages = {
            "win10toast": "Enhanced Windows notifications",
            "pync": "Enhanced macOS notifications",
            "psutil": "System monitoring",
            "keyring": "Secure configuration storage",
        }

        for package, description in optional_packages.items():
            try:
                print(f"   Installing {package} ({description})...")
                subprocess.check_call(
                    [self.python_exe, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"   ✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  {package} installation failed (optional)")
                self.warnings.append(
                    f"Optional package {package} could not be installed"
                )

    def provide_mpv_instructions(self):
        """Provide instructions for installing MPV"""
        print("\n🎵 MPV PLAYER INSTALLATION")
        print("MPV is required for music features. Here's how to install it:")
        print()

        if self.system == "Windows":
            print("Windows:")
            print("1. Download MPV from: https://mpv.io/installation/")
            print("2. Extract to C:\\Program Files\\mpv\\")
            print("3. Or use Chocolatey: choco install mpv")
            print("4. Or use Scoop: scoop install mpv")

        elif self.system == "Darwin":
            print("macOS:")
            print("1. Install Homebrew: https://brew.sh/")
            print("2. Run: brew install mpv")
            print("3. Or use MacPorts: sudo port install mpv")

        elif self.system == "Linux":
            print("Linux:")
            print("Ubuntu/Debian: sudo apt install mpv")
            print("Fedora: sudo dnf install mpv")
            print("Arch: sudo pacman -S mpv")
            print("Snap: sudo snap install mpv")

        print()

    def print_summary(self):
        """Print setup summary"""
        print("\n" + "═" * 70)
        print("                    SETUP SUMMARY")
        print("═" * 70)

        if not self.errors:
            print("🎉 Setup completed successfully!")
            print()
            print("📋 NEXT STEPS:")
            print("1. Run the application:")
            print(f"   python {self.app_dir / 'focus_app.py'}")
            print("2. Or use the desktop shortcut if created")
            print("3. Configure your preferences in the GUI")
            print("4. Start your first focus session!")
            print()
            print("📚 AVAILABLE COMMANDS:")
            print(f"   GUI Mode:       python {self.app_dir / 'focus_app.py'} --gui")
            print(f"   Console Mode:   python {self.app_dir / 'focus_console.py'}")
            print(f"   Dashboard:      python {self.app_dir / 'dashboard.py'} --gui")
            print(
                f"   Quick Session:  python {self.app_dir / 'focus_console.py'} --pomodoro"
            )
        else:
            print("❌ Setup completed with errors:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.check_mpv():
            print()
            self.provide_mpv_instructions()

        print("\n🎯 Happy focusing!")
        print("═" * 70)

    def run_setup(self, skip_deps: bool = False, skip_shortcuts: bool = False):
        """Run the complete setup process"""
        self.print_header()

        success = True

        # Core checks
        success &= self.check_python_version()
        success &= self.check_pip()

        # Dependency installation
        if not skip_deps:
            success &= self.install_dependencies()
            self.install_optional_packages()

        # Setup
        success &= self.setup_directories()
        success &= self.create_default_config()

        # Optional features
        self.check_mpv()

        if not skip_shortcuts:
            self.setup_shortcuts()

        # Verification
        if success:
            success &= self.verify_installation()

        self.print_summary()
        return success


def main():
    """Main setup function"""
    import argparse

    parser = argparse.ArgumentParser(description="Focus Timer Setup Script")
    parser.add_argument(
        "--skip-deps", action="store_true", help="Skip dependency installation"
    )
    parser.add_argument(
        "--skip-shortcuts", action="store_true", help="Skip shortcut creation"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing installation"
    )

    args = parser.parse_args()

    setup = SetupManager()

    if args.verify_only:
        setup.print_header()
        if setup.verify_installation():
            print("✅ Installation is working correctly!")
        else:
            print("❌ Installation has issues")
            sys.exit(1)
    else:
        success = setup.run_setup(
            skip_deps=args.skip_deps, skip_shortcuts=args.skip_shortcuts
        )

        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
    main()
