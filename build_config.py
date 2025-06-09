#!/usr/bin/env python3
"""
Build Configuration for Ultimate Focus Timer
PyInstaller configuration and build utilities
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Build configuration
BUILD_CONFIG = {
    "app_name": "UltimateFocusTimer",
    "main_script": "main.py",
    "icon_file": "files/icon.png",
    "version_file": "src/__version__.py",
    "config_files": [
        "config.yml",
        "static/",
        "music/",
    ],
    "hidden_imports": [
        "PyYAML",
        "plyer.platforms.win.notification",
        "plyer.platforms.macosx.notification",
        "plyer.platforms.linux.notification",
        "matplotlib.backends.backend_tkagg",
        "pandas._libs.tslibs.base",
        "pkg_resources.py2_warn",
    ],
    "exclude_modules": [
        "pytest",
        "black",
        "flake8",
        "mypy",
        "jupyter",
        "notebook",
    ]
}

def get_platform_name():
    """Get platform-specific name for builds"""
    system = platform.system().lower()
    arch = platform.machine().lower()

    if system == "windows":
        return f"windows-{arch}"
    elif system == "darwin":
        return f"macos-{arch}"
    elif system == "linux":
        return f"linux-{arch}"
    else:
        return f"{system}-{arch}"

def create_spec_file():
    """Create PyInstaller spec file"""
    platform_name = get_platform_name()

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('config.yml', '.'),
    ('static', 'static'),
    ('music', 'music'),
    ('files/icon.png', 'files'),
    ('src', 'src'),
]

# Hidden imports for cross-platform compatibility
hiddenimports = {BUILD_CONFIG["hidden_imports"]}

# Analysis configuration
a = Analysis(
    ['{BUILD_CONFIG["main_script"]}'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={BUILD_CONFIG["exclude_modules"]},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary modules
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{BUILD_CONFIG["app_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{BUILD_CONFIG["icon_file"]}' if os.path.exists('{BUILD_CONFIG["icon_file"]}') else None,
)

# macOS App Bundle (optional)
{'app = BUNDLE(exe, name="UltimateFocusTimer.app", icon="files/icon.png", bundle_identifier="com.focustimer.app")' if platform.system() == "Darwin" else ''}
'''

    with open("focus_timer.spec", "w") as f:
        f.write(spec_content)

    print(f"✅ Created PyInstaller spec file for {platform_name}")

def install_build_dependencies():
    """Install required build dependencies"""
    dependencies = [
        "pyinstaller>=5.13.0",
        "auto-py-to-exe>=2.34.0",  # GUI for PyInstaller
    ]

    print("📦 Installing build dependencies...")
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep],
                         check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False

    return True

def build_executable():
    """Build executable using PyInstaller"""
    platform_name = get_platform_name()

    print(f"🔨 Building executable for {platform_name}...")

    # Create spec file
    create_spec_file()

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "focus_timer.spec"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        print(f"📁 Executable location: dist/{BUILD_CONFIG['app_name']}")

        # Create distribution folder
        dist_name = f"UltimateFocusTimer-{platform_name}"
        dist_path = Path("dist") / dist_name

        if dist_path.exists():
            shutil.rmtree(dist_path)

        # Copy executable and required files
        shutil.copytree(Path("dist") / BUILD_CONFIG["app_name"], dist_path)

        # Copy additional files
        additional_files = [
            "README.md",
            "LICENSE",
            "config.yml",
            "docs/",
        ]

        for file_path in additional_files:
            src = Path(file_path)
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, dist_path / src.name, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dist_path / src.name)

        print(f"📦 Distribution package created: {dist_path}")

        # Create ZIP archive
        archive_name = f"{dist_name}.zip"
        shutil.make_archive(dist_name, 'zip', 'dist', dist_name)
        print(f"🗜️ Archive created: {archive_name}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_installer_script():
    """Create platform-specific installer script"""
    platform_name = get_platform_name()

    if platform.system() == "Windows":
        # Create Windows batch installer
        installer_content = '''@echo off
echo Ultimate Focus Timer - Windows Installer
echo ========================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Run setup
echo Running setup...
python setup.py

echo.
echo Installation completed!
echo Run 'UltimateFocusTimer.exe' to start the application
pause
'''
        with open("install.bat", "w") as f:
            f.write(installer_content)

    elif platform.system() == "Darwin":
        # Create macOS installer script
        installer_content = '''#!/bin/bash
echo "Ultimate Focus Timer - macOS Installer"
echo "======================================"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Run setup
echo "Running setup..."
python3 setup.py

echo ""
echo "Installation completed!"
echo "Run './UltimateFocusTimer' to start the application"
'''
        with open("install.sh", "w") as f:
            f.write(installer_content)
        os.chmod("install.sh", 0o755)

    else:  # Linux
        # Create Linux installer script
        installer_content = '''#!/bin/bash
echo "Ultimate Focus Timer - Linux Installer"
echo "====================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

# Install system dependencies
if command -v apt &> /dev/null; then
    echo "Installing system dependencies (Ubuntu/Debian)..."
    sudo apt update
    sudo apt install -y python3-pip python3-tk mpv
elif command -v dnf &> /dev/null; then
    echo "Installing system dependencies (Fedora)..."
    sudo dnf install -y python3-pip python3-tkinter mpv
elif command -v pacman &> /dev/null; then
    echo "Installing system dependencies (Arch)..."
    sudo pacman -S python-pip tk mpv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Run setup
echo "Running setup..."
python3 setup.py

echo ""
echo "Installation completed!"
echo "Run './UltimateFocusTimer' to start the application"
'''
        with open("install.sh", "w") as f:
            f.write(installer_content)
        os.chmod("install.sh", 0o755)

    print(f"✅ Created installer script for {platform_name}")

def main():
    """Main build function"""
    print("🎯 Ultimate Focus Timer - Build System")
    print("====================================")

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "deps":
            install_build_dependencies()
        elif command == "spec":
            create_spec_file()
        elif command == "build":
            if install_build_dependencies():
                build_executable()
        elif command == "installer":
            create_installer_script()
        elif command == "all":
            if install_build_dependencies():
                create_installer_script()
                build_executable()
        else:
            print("Usage: python build_config.py [deps|spec|build|installer|all]")
    else:
        print("Available commands:")
        print("  deps      - Install build dependencies")
        print("  spec      - Create PyInstaller spec file")
        print("  build     - Build executable")
        print("  installer - Create installer script")
        print("  all       - Do everything")
        print("\nUsage: python build_config.py [command]")

if __name__ == "__main__":
    main()
