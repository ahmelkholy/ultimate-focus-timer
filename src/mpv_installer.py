#!/usr/bin/env python3
"""
mpv_installer.py - Cross-platform MPV auto-installer for Ultimate Focus Timer.

Automatically detects and installs MPV if not present.
"""

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class MPVInstaller:
    """Cross-platform MPV installer and detector"""

    def __init__(self):
        self.system = platform.system().lower()
        self.mpv_path: Optional[Path] = None

    def find_mpv(self) -> Optional[Path]:
        """Find MPV executable on the system"""
        # Check common executable names
        mpv_names = ["mpv", "mpv.exe", "mpv.com"]

        # Check if mpv is in PATH
        for name in mpv_names:
            mpv_in_path = shutil.which(name)
            if mpv_in_path:
                self.mpv_path = Path(mpv_in_path)
                logger.info(f"Found MPV at: {self.mpv_path}")
                return self.mpv_path

        # Check common installation directories
        common_dirs = self._get_common_mpv_dirs()
        for directory in common_dirs:
            if not directory.exists():
                continue
            for name in mpv_names:
                mpv_exe = directory / name
                if mpv_exe.exists() and mpv_exe.is_file():
                    self.mpv_path = mpv_exe
                    logger.info(f"Found MPV at: {self.mpv_path}")
                    return self.mpv_path

        logger.warning("MPV not found on system")
        return None

    def _get_common_mpv_dirs(self) -> list:
        """Get common MPV installation directories by platform"""
        common_dirs = []

        if self.system == "windows":
            # Windows common directories
            program_files = [
                Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
                Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            ]
            for pf in program_files:
                common_dirs.extend([pf / "mpv", pf / "MPV"])

            # User-specific directories
            user_home = Path.home()
            common_dirs.extend(
                [
                    user_home / "mpv",
                    user_home / "portable_config",
                    user_home / "AppData" / "Local" / "mpv",
                ]
            )

        elif self.system == "darwin":
            # macOS common directories
            common_dirs.extend(
                [
                    Path("/usr/local/bin"),
                    Path("/opt/homebrew/bin"),
                    Path("/Applications/mpv.app/Contents/MacOS"),
                    Path.home() / "Applications" / "mpv.app" / "Contents" / "MacOS",
                ]
            )

        elif self.system == "linux":
            # Linux common directories
            common_dirs.extend(
                [
                    Path("/usr/bin"),
                    Path("/usr/local/bin"),
                    Path("/opt/mpv"),
                    Path.home() / ".local" / "bin",
                ]
            )

        return common_dirs

    def is_mpv_installed(self) -> bool:
        """Check if MPV is installed and working"""
        mpv = self.find_mpv()
        if not mpv:
            return False

        # Test if MPV actually works
        try:
            result = subprocess.run(
                [str(mpv), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and "mpv" in result.stdout.lower():
                logger.info(f"MPV is working: {result.stdout.split()[0]}")
                return True
        except Exception as e:
            logger.warning(f"MPV test failed: {e}")

        return False

    def install_mpv(self) -> Tuple[bool, str]:
        """
        Install MPV based on the platform.
        Returns: (success: bool, message: str)
        """
        logger.info(f"Installing MPV for {self.system}...")

        try:
            if self.system == "windows":
                return self._install_windows()
            elif self.system == "darwin":
                return self._install_macos()
            elif self.system == "linux":
                return self._install_linux()
            else:
                return False, f"Unsupported platform: {self.system}"
        except Exception as e:
            logger.error(f"MPV installation failed: {e}")
            return False, f"Installation error: {str(e)}"

    def _install_windows(self) -> Tuple[bool, str]:
        """Install MPV on Windows"""
        msg = (
            "Please install MPV manually:\n"
            "1. Download from: https://mpv.io/installation/\n"
            "2. Extract to a folder (e.g., C:\\mpv)\n"
            "3. Add the folder to your PATH or update config.yml with mpv_executable path"
        )
        return False, msg

    def _install_macos(self) -> Tuple[bool, str]:
        """Install MPV on macOS using Homebrew"""
        # Check if Homebrew is installed
        if not shutil.which("brew"):
            msg = (
                "Homebrew not found. Please install Homebrew first:\n"
                '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"\n'
                "Then run: brew install mpv"
            )
            return False, msg

        try:
            logger.info("Installing MPV via Homebrew...")
            result = subprocess.run(
                ["brew", "install", "mpv"],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            if result.returncode == 0:
                # Verify installation
                if self.is_mpv_installed():
                    return True, "MPV installed successfully via Homebrew!"
                else:
                    return False, "MPV installation completed but verification failed"
            else:
                return False, f"Homebrew installation failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return (
                False,
                "Installation timed out. Please install manually: brew install mpv",
            )
        except Exception as e:
            return False, f"Installation error: {str(e)}"

    def _install_linux(self) -> Tuple[bool, str]:
        """Install MPV on Linux using package manager"""
        # Detect package manager
        pkg_managers = {
            "apt-get": ["sudo", "apt-get", "install", "-y", "mpv"],
            "apt": ["sudo", "apt", "install", "-y", "mpv"],
            "dnf": ["sudo", "dnf", "install", "-y", "mpv"],
            "yum": ["sudo", "yum", "install", "-y", "mpv"],
            "pacman": ["sudo", "pacman", "-S", "--noconfirm", "mpv"],
            "zypper": ["sudo", "zypper", "install", "-y", "mpv"],
        }

        for pm, cmd in pkg_managers.items():
            if shutil.which(pm):
                try:
                    logger.info(f"Installing MPV via {pm}...")
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=300, check=False
                    )

                    if result.returncode == 0:
                        # Verify installation
                        if self.is_mpv_installed():
                            return True, f"MPV installed successfully via {pm}!"
                        else:
                            return (
                                False,
                                "MPV installation completed but verification failed",
                            )
                    else:
                        logger.warning(f"{pm} installation failed: {result.stderr}")
                        continue

                except subprocess.TimeoutExpired:
                    return (
                        False,
                        f"Installation timed out. Please install manually: {' '.join(cmd)}",
                    )
                except Exception as e:
                    logger.warning(f"{pm} installation error: {e}")
                    continue

        # If we get here, no package manager worked
        msg = (
            "Could not auto-install MPV. Please install manually:\n"
            "Ubuntu/Debian: sudo apt install mpv\n"
            "Fedora: sudo dnf install mpv\n"
            "Arch: sudo pacman -S mpv"
        )
        return False, msg

    def ensure_mpv_available(
        self, auto_install: bool = True
    ) -> Tuple[bool, str, Optional[Path]]:
        """
        Ensure MPV is available, optionally installing it.
        Returns: (is_available: bool, message: str, mpv_path: Optional[Path])
        """
        # First, check if already installed
        if self.is_mpv_installed():
            return True, "MPV is already installed", self.mpv_path

        if not auto_install:
            return False, "MPV not found and auto-install disabled", None

        # Try to install
        success, msg = self.install_mpv()
        if success:
            # Verify and get path
            if self.is_mpv_installed():
                return True, msg, self.mpv_path
            else:
                return False, "Installation succeeded but MPV not found", None
        else:
            return False, msg, None


def check_and_install_mpv(auto_install: bool = True) -> Tuple[bool, Optional[Path]]:
    """
    Convenience function to check and install MPV.
    Returns: (success: bool, mpv_path: Optional[Path])
    """
    installer = MPVInstaller()
    is_available, message, mpv_path = installer.ensure_mpv_available(auto_install)

    if is_available:
        logger.info(message)
        return True, mpv_path
    else:
        logger.warning(message)
        return False, None


if __name__ == "__main__":
    # Test the installer
    logging.basicConfig(level=logging.INFO)
    print("Testing MPV Installer...")
    print("-" * 50)

    installer = MPVInstaller()

    # Check if installed
    print("Checking for MPV...")
    if installer.is_mpv_installed():
        print(f"✓ MPV found at: {installer.mpv_path}")
    else:
        print("✗ MPV not found")
        print("\nAttempting installation...")
        success, msg = installer.install_mpv()
        print(f"\nResult: {msg}")

        if success:
            print(f"✓ MPV installed at: {installer.mpv_path}")
        else:
            print("✗ Installation failed or requires manual steps")
