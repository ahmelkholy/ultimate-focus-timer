# Release Process

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
