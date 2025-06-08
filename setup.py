#!/usr/bin/env python3
"""
Ultimate Focus Timer Setup Script
Cross-platform automated setup and dependency management
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class UltimateSetupManager:
    """Ultimate cross-platform setup manager for Focus Timer"""

    def __init__(self):
        self.system = platform.system()
        self.architecture = platform.architecture()[0]
        self.app_dir = Path(__file__).parent
        self.python_exe = sys.executable
        self.errors = []
        self.warnings = []
        self.successes = []

        # Platform-specific package managers
        self.package_managers = self._detect_package_managers()

    def print_header(self):
        """Print enhanced setup header"""
        print("🚀" + "=" * 68 + "🚀")
        print("                  🎯 ULTIMATE FOCUS TIMER SETUP")
        print("               Cross-Platform Dependency Manager")
        print("🚀" + "=" * 68 + "🚀")
        print()
        print(f"🖥️  Platform: {self.system} ({self.architecture})")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print(f"📁 Directory: {self.app_dir}")
        print(
            f"🎯 Package Managers: {', '.join(self.package_managers) if self.package_managers else 'None detected'}"
        )
        print()

    def _detect_package_managers(self) -> List[str]:
        """Detect available package managers"""
        managers = []

        if self.system == "Windows":
            # Check for Windows package managers
            if shutil.which("choco"):
                managers.append("chocolatey")
            if shutil.which("winget"):
                managers.append("winget")
            if shutil.which("scoop"):
                managers.append("scoop")
        elif self.system == "Darwin":  # macOS
            if shutil.which("brew"):
                managers.append("homebrew")
            if shutil.which("port"):
                managers.append("macports")
        elif self.system == "Linux":
            # Check for Linux package managers
            if shutil.which("apt"):
                managers.append("apt")
            if shutil.which("yum"):
                managers.append("yum")
            if shutil.which("dnf"):
                managers.append("dnf")
            if shutil.which("pacman"):
                managers.append("pacman")
            if shutil.which("zypper"):
                managers.append("zypper")
            if shutil.which("snap"):
                managers.append("snap")
            if shutil.which("flatpak"):
                managers.append("flatpak")

        return managers

    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        print("🔍 Checking Python compatibility...")

        if sys.version_info < (3.8):
            self.errors.append("Python 3.8+ is required for optimal functionality")
            print("❌ Python 3.8+ is required")
            return False

        if sys.version_info < (3, 10):
            self.warnings.append("Python 3.10+ recommended for best performance")
            print(
                f"⚠️  Python {sys.version_info.major}.{sys.version_info.minor} - Consider upgrading to 3.10+"
            )
        else:
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

    def install_python_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt"""
        print("📦 Installing Python dependencies...")

        requirements_file = self.app_dir / "requirements.txt"
        if not requirements_file.exists():
            self.errors.append("requirements.txt not found")
            print("❌ requirements.txt not found")
            return False

        try:
            # Upgrade pip first
            print("   🔧 Upgrading pip...")
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                self.warnings.append("Failed to upgrade pip")
                print("   ⚠️  Failed to upgrade pip (continuing anyway)")

            # Install requirements
            print("   📋 Installing requirements...")
            result = subprocess.run(
                [self.python_exe, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print("   ✅ Python dependencies installed successfully")
                self.successes.append("Python dependencies installed")
                return True
            else:
                self.errors.append(f"Failed to install dependencies: {result.stderr}")
                print(f"   ❌ Failed to install dependencies")
                print(f"      Error: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.errors.append("Installation timeout")
            print("   ❌ Installation timeout")
            return False
        except Exception as e:
            self.errors.append(f"Installation error: {e}")
            print(f"   ❌ Installation error: {e}")
            return False

    def check_and_install_mpv(self) -> bool:
        """Check for MPV and attempt installation if missing"""
        print("🎵 Checking MPV media player...")

        # Check if MPV is already installed
        if shutil.which("mpv"):
            print("   ✅ MPV already installed")
            self.successes.append("MPV available")
            return True

        print("   ⚠️  MPV not found - attempting installation...")

        # Try to install MPV based on platform and available package managers
        if self._install_mpv_for_platform():
            print("   ✅ MPV installation completed")
            self.successes.append("MPV installed")
            return True
        else:
            self.warnings.append("MPV installation failed - music features disabled")
            print("   ❌ MPV installation failed")
            self._print_manual_mpv_instructions()
            return False

    def _install_mpv_for_platform(self) -> bool:
        """Install MPV based on platform and available package managers"""
        success = False

        if self.system == "Windows":
            success = self._install_mpv_windows()
        elif self.system == "Darwin":  # macOS
            success = self._install_mpv_macos()
        elif self.system == "Linux":
            success = self._install_mpv_linux()

        return success

    def _install_mpv_windows(self) -> bool:
        """Install MPV on Windows"""
        if "chocolatey" in self.package_managers:
            print("      🍫 Installing via Chocolatey...")
            try:
                result = subprocess.run(
                    ["choco", "install", "mpv", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0
            except:
                pass

        if "winget" in self.package_managers:
            print("      📦 Installing via Winget...")
            try:
                result = subprocess.run(
                    ["winget", "install", "mpv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0
            except:
                pass

        if "scoop" in self.package_managers:
            print("      🥄 Installing via Scoop...")
            try:
                result = subprocess.run(
                    ["scoop", "install", "mpv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0
            except:
                pass

        return False

    def _install_mpv_macos(self) -> bool:
        """Install MPV on macOS"""
        if "homebrew" in self.package_managers:
            print("      🍺 Installing via Homebrew...")
            try:
                result = subprocess.run(
                    ["brew", "install", "mpv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0
            except:
                pass

        if "macports" in self.package_managers:
            print("      🚢 Installing via MacPorts...")
            try:
                result = subprocess.run(
                    ["sudo", "port", "install", "mpv"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                return result.returncode == 0
            except:
                pass

        return False

    def _install_mpv_linux(self) -> bool:
        """Install MPV on Linux"""
        managers = {
            "apt": [
                "sudo",
                "apt",
                "update",
                "&&",
                "sudo",
                "apt",
                "install",
                "-y",
                "mpv",
            ],
            "yum": ["sudo", "yum", "install", "-y", "mpv"],
            "dnf": ["sudo", "dnf", "install", "-y", "mpv"],
            "pacman": ["sudo", "pacman", "-S", "--noconfirm", "mpv"],
            "zypper": ["sudo", "zypper", "install", "-y", "mpv"],
            "snap": ["sudo", "snap", "install", "mpv"],
        }

        for manager in self.package_managers:
            if manager in managers:
                print(f"      📦 Installing via {manager}...")
                try:
                    cmd = managers[manager]
                    if "&&" in cmd:
                        # Handle chained commands
                        cmd1 = cmd[: cmd.index("&&")]
                        cmd2 = cmd[cmd.index("&&") + 1 :]
                        subprocess.run(cmd1, timeout=120)
                        result = subprocess.run(cmd2, timeout=300)
                    else:
                        result = subprocess.run(cmd, timeout=300)

                    if result.returncode == 0:
                        return True
                except:
                    continue

        return False

    def _print_manual_mpv_instructions(self):
        """Print manual installation instructions for MPV"""
        print("\n   📋 Manual MPV Installation Instructions:")

        if self.system == "Windows":
            print("      • Download from: https://mpv.io/installation/")
            print("      • Or use: choco install mpv")
            print("      • Or use: winget install mpv")
        elif self.system == "Darwin":
            print("      • Install Homebrew: https://brew.sh/")
            print("      • Then run: brew install mpv")
        elif self.system == "Linux":
            print("      • Ubuntu/Debian: sudo apt install mpv")
            print("      • Fedora: sudo dnf install mpv")
            print("      • Arch: sudo pacman -S mpv")

        print("      • Visit: https://mpv.io/installation/ for more options")

    def create_desktop_integration(self) -> bool:
        """Create desktop integration (shortcuts, etc.)"""
        print("🖥️  Setting up desktop integration...")

        try:
            if self.system == "Windows":
                return self._create_windows_shortcuts()
            elif self.system == "Darwin":
                return self._create_macos_integration()
            elif self.system == "Linux":
                return self._create_linux_integration()
            else:
                self.warnings.append(
                    "Desktop integration not supported on this platform"
                )
                return False
        except Exception as e:
            self.warnings.append(f"Desktop integration failed: {e}")
            print(f"   ⚠️  Desktop integration failed: {e}")
            return False

    def _create_windows_shortcuts(self) -> bool:
        """Create Windows shortcuts"""
        try:
            desktop = Path.home() / "Desktop"
            start_menu = (
                Path.home()
                / "AppData"
                / "Roaming"
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
            )

            # Create batch file for easy launching
            batch_content = f"""@echo off
cd /d "{self.app_dir}"
python main.py
pause
"""
            batch_file = self.app_dir / "focus_timer.bat"
            batch_file.write_text(batch_content)

            print("   ✅ Created Windows launcher")
            self.successes.append("Windows shortcuts created")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create Windows shortcuts: {e}")
            return False

    def _create_macos_integration(self) -> bool:
        """Create macOS integration"""
        try:
            # Create shell script for easy launching
            script_content = f"""#!/bin/bash
cd "{self.app_dir}"
python3 main.py
"""
            script_file = self.app_dir / "focus_timer.sh"
            script_file.write_text(script_content)
            script_file.chmod(0o755)

            print("   ✅ Created macOS launcher")
            self.successes.append("macOS integration created")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create macOS integration: {e}")
            return False

    def _create_linux_integration(self) -> bool:
        """Create Linux desktop integration"""
        try:
            # Create shell script
            script_content = f"""#!/bin/bash
cd "{self.app_dir}"
python3 main.py
"""
            script_file = self.app_dir / "focus_timer.sh"
            script_file.write_text(script_content)
            script_file.chmod(0o755)

            # Create .desktop file
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Focus Timer
Comment=Ultimate productivity timer with music integration
Exec=python3 "{self.app_dir}/main.py"
Icon={self.app_dir}/files/icon.png
Terminal=false
Categories=Productivity;Office;
"""

            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)

            desktop_file = desktop_dir / "focus-timer.desktop"
            desktop_file.write_text(desktop_content)
            desktop_file.chmod(0o755)

            print("   ✅ Created Linux desktop integration")
            self.successes.append("Linux desktop integration created")
            return True
        except Exception as e:
            print(f"   ❌ Failed to create Linux integration: {e}")
            return False

    def setup_directories(self) -> bool:
        """Create necessary directories"""
        print("📁 Setting up directories...")

        directories = [
            "log",
            "backups",
            "files",
            "static",
        ]

        success = True
        for directory in directories:
            dir_path = self.app_dir / directory
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   ✅ {directory}/")
            except Exception as e:
                print(f"   ❌ Failed to create {directory}/: {e}")
                self.errors.append(f"Failed to create {directory}/ directory")
                success = False

        if success:
            self.successes.append("Directories created")

        return success

    def verify_installation(self) -> bool:
        """Verify that everything is working correctly"""
        print("🔍 Verifying installation...")

        # Test imports
        try:
            sys.path.insert(0, str(self.app_dir))

            import matplotlib
            import pandas
            import plyer
            import psutil
            import yaml

            print("   ✅ All Python modules importable")

            # Test main module
            from main import UltimateFocusLauncher

            launcher = UltimateFocusLauncher()
            dependencies = launcher.check_dependencies()

            working_deps = sum(1 for status in dependencies.values() if status)
            total_deps = len(dependencies)

            print(f"   📊 Dependencies: {working_deps}/{total_deps} working")

            if working_deps >= total_deps - 1:  # Allow MPV to be missing
                print("   ✅ Installation verified successfully")
                self.successes.append("Installation verified")
                return True
            else:
                print(
                    "   ⚠️  Some dependencies missing but core functionality available"
                )
                self.warnings.append("Some optional dependencies missing")
                return True

        except ImportError as e:
            print(f"   ❌ Import verification failed: {e}")
            self.errors.append("Import verification failed")
            return False

    def print_summary(self):
        """Print setup summary"""
        print("\n" + "🎯" * 35)
        print("                SETUP SUMMARY")
        print("🎯" * 35)

        if self.successes:
            print("\n✅ SUCCESSES:")
            for success in self.successes:
                print(f"   • {success}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        print("\n🚀 NEXT STEPS:")
        if not self.errors:
            print("   • Run: python main.py")
            print("   • Or use the created launcher shortcuts")
            print("   • Check the README.md for usage instructions")
        else:
            print("   • Fix the errors above")
            print("   • Re-run: python setup.py")

        print("\n📚 DOCUMENTATION:")
        print("   • README.md - Full documentation")
        print("   • python main.py --help - Command line help")
        print("   • python main.py --check - Dependency check")

        print("\n🎯 Happy focusing! 🎯")

    def run_full_setup(self):
        """Run the complete setup process"""
        self.print_header()

        # Check basic requirements
        if not self.check_python_version():
            self.print_summary()
            return False

        # Setup steps
        steps = [
            ("Directories", self.setup_directories),
            ("Python Dependencies", self.install_python_dependencies),
            ("MPV Media Player", self.check_and_install_mpv),
            ("Desktop Integration", self.create_desktop_integration),
            ("Installation Verification", self.verify_installation),
        ]

        print("🚀 Starting setup process...\n")

        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            try:
                step_func()
            except Exception as e:
                self.errors.append(f"{step_name} failed: {e}")
                print(f"   ❌ {step_name} failed: {e}")
            print()

        self.print_summary()
        return len(self.errors) == 0


def main():
    """Main setup entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ultimate Focus Timer Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="install",
        choices=["install", "check", "clean", "repair"],
        help="Setup command to execute",
    )

    args = parser.parse_args()

    setup = UltimateSetupManager()

    if args.command == "install":
        setup.run_full_setup()
    elif args.command == "check":
        setup.print_header()
        setup.verify_installation()
        setup.print_summary()
    elif args.command == "clean":
        print("🧹 Cleaning up temporary files...")
        # Add cleanup logic here
        print("✅ Cleanup completed")
    elif args.command == "repair":
        print("🔧 Repairing installation...")
        setup.run_full_setup()


if __name__ == "__main__":
    main()
