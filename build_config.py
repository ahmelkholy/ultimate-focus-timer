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
        # tkinter imports
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.simpledialog",
        "tkinter.font",
        "tkinter.colorchooser",
        # PIL/Pillow imports
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        # Additional matplotlib backends
        "matplotlib.backends._backend_agg",
        "matplotlib.figure",
        "matplotlib.backends.backend_agg",
        # Pandas and numpy
        "pandas.plotting",
        "pandas.plotting._matplotlib",
        "numpy.random.common",
        "numpy.random.bounded_integers",
        "numpy.random.entropy",
        # Seaborn for data visualization
        "seaborn",
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
from PyInstaller.utils.hooks import collect_submodules

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
hiddenimports = {BUILD_CONFIG["hidden_imports"]} + collect_submodules("seaborn")

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
    # ensure all runtime dependencies are installed
    print("📦 Installing runtime dependencies from requirements.txt...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    # Create spec file
    create_spec_file()

    # Ensure required directories exist
    for directory in ["music", "log", "backups", "static"]:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"  📁 Created directory: {directory}")

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
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

def setup_github_workflows():
    """Set up GitHub Actions workflows for building executables"""
    print("🚀 Setting up GitHub Actions workflows...")

    # Create .github/workflows directory if it doesn't exist
    workflows_dir = Path(".github/workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)

    # Create workflow for Windows only
    windows_workflow = workflows_dir / "build-windows-exe.yml"
    with open(windows_workflow, "w") as f:
        f.write("""name: Build Windows Executable

on:
  workflow_dispatch:  # Allows manual triggering from GitHub UI
  push:
    tags:
      - 'v*'  # Run workflow when a new tag is pushed
  release:
    types: [created]

jobs:
  build-windows:
    runs-on: windows-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-build.txt

    - name: Create directories
      run: |
        mkdir -p music
        mkdir -p log
        mkdir -p backups
        mkdir -p static

    - name: Build executable
      run: |
        python build_config.py build

    - name: Archive executable
      uses: actions/upload-artifact@v4
      with:
        name: UltimateFocusTimer-windows
        path: dist/UltimateFocusTimer*

    - name: Upload to Release
      if: github.event_name == 'release' || startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/UltimateFocusTimer*.zip
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")

    # Create workflow for all platforms
    all_platforms_workflow = workflows_dir / "build-all-platforms.yml"
    with open(all_platforms_workflow, "w") as f:
        f.write("""name: Build Releases

on:
  workflow_dispatch:  # Allows manual triggering from GitHub UI
  push:
    tags:
      - 'v*'  # Run workflow when a new tag is pushed
  release:
    types: [created]

jobs:
  build-windows:
    runs-on: windows-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-build.txt

    - name: Create directories
      run: |
        mkdir -p music
        mkdir -p log
        mkdir -p backups
        mkdir -p static

    - name: Build executable
      run: |
        python build_config.py build

    - name: Archive executable
      uses: actions/upload-artifact@v4
      with:
        name: UltimateFocusTimer-windows
        path: dist/UltimateFocusTimer*

    - name: Upload to Release
      if: github.event_name == 'release' || startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: |
          dist/UltimateFocusTimer*.zip
          dist/UltimateFocusTimer*.exe
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  build-macos:
    runs-on: macos-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-build.txt
        brew install mpv

    - name: Create directories
      run: |
        mkdir -p music
        mkdir -p log
        mkdir -p backups
        mkdir -p static

    - name: Build executable
      run: |
        python build_config.py build

    - name: Archive executable
      uses: actions/upload-artifact@v4
      with:
        name: UltimateFocusTimer-macos
        path: dist/UltimateFocusTimer*

    - name: Upload to Release
      if: github.event_name == 'release' || startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/UltimateFocusTimer*.zip
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  build-linux:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'

    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y python3-dev python3-tk mpv
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-build.txt

    - name: Create directories
      run: |
        mkdir -p music
        mkdir -p log
        mkdir -p backups
        mkdir -p static

    - name: Build executable
      run: |
        python build_config.py build

    - name: Archive executable
      uses: actions/upload-artifact@v4
      with:
        name: UltimateFocusTimer-linux
        path: dist/UltimateFocusTimer*

    - name: Upload to Release
      if: github.event_name == 'release' || startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: dist/UltimateFocusTimer*.zip
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
""")

    print(f"✅ Created GitHub workflow for Windows: {windows_workflow}")
    print(f"✅ Created GitHub workflow for all platforms: {all_platforms_workflow}")

    # Create RELEASE.md file
    release_md = Path("docs/RELEASE.md")
    release_md.parent.mkdir(exist_ok=True)
    with open(release_md, "w") as f:
        f.write("""# Release Process

This document explains how to create releases for Ultimate Focus Timer, including building executables for different platforms.

## Creating a New Release

### 1. Update Version

Update the version number in `src/__version__.py`:

```python
__version__ = "1.0.0"  # Change this to the new version
```

### 2. Update Changelog

Update the `docs/CHANGELOG.md` file with details of the changes in this new release.

### 3. Create a Git Tag

```bash
git add src/__version__.py docs/CHANGELOG.md
git commit -m "Bump version to X.Y.Z"
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin main --tags
```

### 4. GitHub Release

Once you push the tag, the GitHub Actions workflow will automatically:

1. Build executables for Windows, macOS, and Linux
2. Upload them as artifacts
3. Attach them to the release if created through the GitHub interface

Alternatively, you can create a new release through the GitHub interface:

1. Go to the repository on GitHub
2. Click on "Releases"
3. Click "Draft a new release"
4. Choose the tag you just created
5. Add release notes (you can copy from the changelog)
6. Click "Publish release"

The workflow will automatically attach the built executables to this release.

## Manual Building

If you need to build executables manually:

### Windows

```powershell
# Ensure you're in a virtual environment with dependencies installed
python -m pip install -r requirements.txt -r requirements-build.txt

# Build the executable
python build_config.py build
```

### macOS

```bash
# Install dependencies
brew install mpv
python -m pip install -r requirements.txt -r requirements-build.txt

# Build the executable
python build_config.py build
```

### Linux

```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt install python3-dev python3-tk mpv
# Fedora:
sudo dnf install python3-devel python3-tkinter mpv
# Arch:
sudo pacman -S python-pip tk mpv

# Install Python dependencies
python -m pip install -r requirements.txt -r requirements-build.txt

# Build the executable
python build_config.py build
```

The built executables will be available in the `dist/` directory.
""")

    print(f"✅ Created release guide: {release_md}")

    return True

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
        elif command == "github":
            setup_github_workflows()
        else:
            print("Usage: python build_config.py [deps|spec|build|installer|all|github]")
    else:
        print("Available commands:")
        print("  deps      - Install build dependencies")
        print("  spec      - Create PyInstaller spec file")
        print("  build     - Build executable")
        print("  installer - Create installer script")
        print("  github    - Setup GitHub Actions workflows")
        print("  all       - Do everything")
        print("\nUsage: python build_config.py [command]")

if __name__ == "__main__":
    # Install build dependencies and build executable
    if install_build_dependencies():
        try:
            build_executable()
        except Exception as e:
            print(f"❌ Build failed: {e}")
            sys.exit(1)
    else:
        print("❌ Could not install build dependencies")
        sys.exit(1)
