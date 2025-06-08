#!/usr/bin/env python3
"""
Ultimate Focus Timer - Quick Installation Script
Automated setup for new users
"""

import os
import platform
import subprocess
import sys
import urllib.request
from pathlib import Path


def print_header():
    """Print installation header"""
    print("=" * 60)
    print("🎯 Ultimate Focus Timer - Quick Installation")
    print("=" * 60)
    print()


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Found: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
    return True


def check_git():
    """Check if git is available"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        print_success("Git available ✓")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Git not found. Please install Git first.")
        return False


def install_package():
    """Install the package"""
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                      check=True, capture_output=True)

        # Install from current directory
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."],
                      check=True)
        print_success("Package installed successfully ✓")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Installation failed: {e}")
        return False


def setup_virtual_environment():
    """Set up virtual environment"""
    venv_path = Path(".venv")

    if venv_path.exists():
        print_info("Virtual environment already exists")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print_success("Virtual environment created ✓")

        # Provide activation instructions
        system = platform.system()
        if system == "Windows":
            activate_cmd = ".venv\\Scripts\\activate"
        else:
            activate_cmd = "source .venv/bin/activate"

        print_info(f"Activate with: {activate_cmd}")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Virtual environment creation failed: {e}")
        return False


def install_dependencies():
    """Install project dependencies"""
    try:
        # Install requirements
        if Path("requirements.txt").exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                          check=True, capture_output=True)
            print_success("Dependencies installed ✓")

        # Install development dependencies if requested
        if Path("requirements-dev.txt").exists():
            response = input("Install development dependencies? (y/N): ").lower()
            if response in ['y', 'yes']:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"],
                              check=True, capture_output=True)
                print_success("Development dependencies installed ✓")

        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Dependency installation failed: {e}")
        return False


def test_installation():
    """Test if installation was successful"""
    try:
        # Test basic import
        subprocess.run([sys.executable, "-c",
                       "import sys; sys.path.insert(0, 'src'); from config_manager import ConfigManager; print('Import test passed')"],
                      check=True, capture_output=True)

        # Test main script
        result = subprocess.run([sys.executable, "main.py", "--help"],
                               capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Installation test passed ✓")
            return True
        else:
            print_error("Installation test failed")
            return False

    except subprocess.CalledProcessError as e:
        print_error(f"Installation test failed: {e}")
        return False


def show_next_steps():
    """Show next steps to user"""
    print()
    print("🎉 Installation Complete!")
    print("-" * 30)
    print()
    print("Next steps:")
    print("1. Read the user guide: docs/USER_GUIDE.md")
    print("2. Start the timer: python main.py")
    print("3. Try GUI mode: python main.py --gui")
    print("4. View statistics: python main.py --stats")
    print("5. See all options: python main.py --help")
    print()
    print("For development:")
    print("- Windows: .\\dev.ps1 help")
    print("- Unix/Mac: make help")
    print()
    print("Documentation: docs/")
    print("Report issues: GitHub Issues")
    print()


def main():
    """Main installation process"""
    print_header()

    # Check requirements
    if not check_python_version():
        sys.exit(1)

    # Optional git check (for development)
    git_available = check_git()

    # Set up virtual environment
    print_info("Setting up virtual environment...")
    if not setup_virtual_environment():
        print_error("Virtual environment setup failed")
        # Continue anyway, user might want system-wide install

    # Install dependencies
    print_info("Installing dependencies...")
    if not install_dependencies():
        sys.exit(1)

    # Install package
    print_info("Installing Ultimate Focus Timer...")
    if not install_package():
        sys.exit(1)

    # Test installation
    print_info("Testing installation...")
    if not test_installation():
        print_error("Installation test failed, but package may still work")

    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()
