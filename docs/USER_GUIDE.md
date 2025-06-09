# 🎯 Ultimate Focus Timer - Complete Documentation

Welcome to the comprehensive documentation for Ultimate Focus Timer, a cross-platform productivity application built with Python.

## 📚 Table of Contents

1. **[Quick Start](#-quick-start)**
2. **[Installation Guide](#-installation-guide)**
3. **[User Interfaces](#-user-interfaces)**
4. **[Configuration](#-configuration)**
5. **[Music Integration](#-music-integration)**
6. **[Analytics & Insights](#-analytics--insights)**
7. **[Advanced Features](#-advanced-features)**
8. **[Troubleshooting](#-troubleshooting)**
9. **[Development](#-development)**

## 🚀 Quick Start

### Windows Executable (Recommended)

The fastest way to get started on Windows:

1. Download the latest `UltimateFocusTimer-windows-x64.zip` from the [Releases page](https://github.com/ahmelkholy/ultimate-focus-timer/releases)
2. Extract the ZIP file to any location
3. Run `UltimateFocusTimer.exe`

No Python installation or setup required!

### Prerequisites (For source installation)

- **Python 3.8+** (Python 3.10+ recommended for best performance)
- **MPV Media Player** (automatically installed by setup script)
- **Internet connection** (for initial setup and music streaming)

### 5-Minute Setup (Source installation)

```bash
# 1. Navigate to project directory
cd "ultimate-focus-timer"

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run automated setup
python setup.py

# 6. Launch application
python main.py
```

## 📦 Installation Guide

### Pre-Built Executables (Recommended)

#### Windows

1. Download the latest `UltimateFocusTimer-windows-x64.zip` from the [Releases page](https://github.com/ahmelkholy/ultimate-focus-timer/releases)
2. Extract the ZIP file to any location
3. Run `UltimateFocusTimer.exe`

#### macOS

1. Download the latest `UltimateFocusTimer-macos.zip` from the [Releases page](https://github.com/ahmelkholy/ultimate-focus-timer/releases)
2. Extract the ZIP file
3. Run `UltimateFocusTimer` application

#### Linux

1. Download the latest `UltimateFocusTimer-linux.zip` from the [Releases page](https://github.com/ahmelkholy/ultimate-focus-timer/releases)
2. Extract the ZIP file
3. Run `./UltimateFocusTimer`

### Source Installation

The automated setup script handles all dependencies and configuration:

```bash
python setup.py
```

**What the setup does:**

- Checks Python compatibility
- Installs MPV media player (cross-platform)
- Verifies all Python dependencies
- Creates desktop integration
- Tests the installation

## 🖥️ User Interfaces

### Interactive Launcher (Default)

```bash
python main.py
```

### GUI Interface

```bash
python main.py --gui
```

### Console Interface

```bash
python main.py --console
```

### Analytics Dashboard

```bash
python main.py --dashboard
```

## ⚙️ Configuration

All settings are stored in `config.yml`:

```yaml
# Session Timings
work_mins: 25
short_break_mins: 5
long_break_mins: 15

# Music Settings
classical_music: true
classical_music_volume: 70
fade_music_transitions: true

# Interface Settings
dark_theme: true
accent_color: "#00ff00"
animated_transitions: true
```

## 🎵 Music Integration

The application supports multiple audio sources and provides seamless background music during focus sessions.

## 📊 Analytics & Insights

Comprehensive productivity tracking with visual charts and export capabilities.

## 🛠️ Troubleshooting

### Common Issues

For detailed troubleshooting, see the main documentation files.

## 🔧 Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

**Thank you for using Ultimate Focus Timer! 🎯**
