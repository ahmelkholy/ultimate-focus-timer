# 🎯 Ultimate Focus Timer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Cross Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/ahmelkholy/ultimate-focus-timer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, cross-platform productivity timer application implementing the Pomodoro Technique with classical music integration, multiple interfaces, and detailed analytics. Built with pure Python for maximum compatibility and ease of use.

## ✨ Key Features

- **🎮 Multiple Interfaces**: GUI, Console, Dashboard, and Interactive Launcher
- **🎵 Music Integration**: Classical music playback with cross-platform audio support
- **📊 Analytics & Tracking**: Comprehensive session logging and productivity insights
- **🔔 Smart Notifications**: Cross-platform desktop notifications with early warnings
- **⚙️ Highly Configurable**: YAML-based configuration with theme support
- **🌍 Cross-Platform**: Windows, macOS, and Linux support

## 💻 Download & Installation

### Windows Executable

The easiest way to use Ultimate Focus Timer on Windows is to download the pre-built executable:

1. Go to the [Releases](https://github.com/ahmelkholy/ultimate-focus-timer/releases) page
2. Download the latest `UltimateFocusTimer-windows-x64.zip` file
3. Extract the ZIP file
4. Run `UltimateFocusTimer.exe`

No installation or Python environment required!

### Other Platforms

For macOS and Linux users, please see the [Installation Guide](docs/USER_GUIDE.md#installation) for platform-specific instructions.

## 📸 Screenshots

### GUI Interface

![Console Interface](files/Screenshot%202025-06-09%20165707.png)

### Console Interface

![GUI Interface](files/Screenshot%202025-06-09%20165653.png)

### Dashboard Analytics

![Dashboard Analytics](files/Screenshot%202025-06-09%20165754.png)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/ahmelkholy/ultimate-focus-timer.git
cd ultimate-focus-timer

# Set up virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run setup
python setup.py

# Launch the application
python main.py
```

## 📖 Documentation

- **[Complete Documentation](docs/README.md)** - Full user guide and features
- **[Virtual Environment Setup](docs/VENV_SETUP.md)** - Detailed environment configuration
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](docs/CHANGELOG.md)** - Version history and updates

## 🎯 Quick Launch Commands

```bash
python main.py                    # Interactive launcher
python main.py --gui             # GUI interface
python main.py --console         # Console interface
python main.py --dashboard       # Analytics dashboard
python main.py --pomodoro        # Quick 25-minute session
python main.py --work 30         # Custom work session
python main.py --info            # System information
```

## 🛠️ System Requirements

- **Python 3.8+** (Python 3.10+ recommended)
- **MPV Media Player** (auto-installed by setup script)
- **Supported Platforms**: Windows 10/11, macOS 10.14+, Linux

## 📦 Installation

### Automatic Setup (Recommended)

```bash
python setup.py
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install MPV (Windows with Chocolatey)
choco install mpv

# Install MPV (macOS with Homebrew)
brew install mpv

# Install MPV (Linux)
sudo apt install mpv  # Ubuntu/Debian
sudo dnf install mpv  # Fedora
```

## 🏗️ Building the Executable

```bash
# Ensure dependencies are installed
python -m pip install -r requirements.txt

# Build a standalone one-file executable
python build_config.py
```

The generated executable will be located in the `dist/UltimateFocusTimer` directory.

## 🎵 Music Features

- **Classical Music Integration**: Automatic background music during work sessions
- **Cross-Platform Audio**: Powered by MPV for consistent experience across platforms
- **Volume Control**: Adjustable music levels with smooth fade transitions
- **Multiple Playlists**: Curated classical, baroque, and piano collections
- **Custom Playlists**: Support for local files and online streams

## 📊 Analytics & Insights

- **Session Tracking**: Automatic logging of all timer sessions
- **Productivity Metrics**: Completion rates, trends, and scoring
- **Visual Analytics**: Beautiful charts and graphs
- **Export Options**: CSV export for external analysis
- **Goal Tracking**: Progress monitoring and achievement tracking

## ⚙️ Configuration

Edit `config.yml` to customize:

```yaml
# Session Settings
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

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Francesco Cirillo** for the Pomodoro Technique
- **MPV Media Player** for excellent cross-platform audio support
- **Python Community** for the amazing ecosystem

---

**Stay focused and productive! 🎯**

_Built with ❤️ for productivity enthusiasts worldwide_
