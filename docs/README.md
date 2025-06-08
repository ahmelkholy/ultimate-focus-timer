# 🎯 Ultimate Focus Timer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Cross Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/yourusername/ultimate-focus-timer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, cross-platform productivity timer application implementing the Pomodoro Technique with classical music integration, multiple interfaces, and detailed analytics. Built with pure Python for maximum compatibility and ease of use.

## ✨ Key Features

### 🎮 Multiple Interfaces

- **GUI Mode**: Beautiful visual interface with progress bars and real-time statistics
- **Console Mode**: Terminal-based interface perfect for developers and CLI enthusiasts  
- **Dashboard**: Comprehensive analytics with charts, insights, and export capabilities
- **Interactive Launcher**: Smart menu system for easy mode selection

### 🎵 Music Integration

- **Classical Music Playback**: Automatic background music during work sessions
- **Cross-Platform Audio**: Powered by MPV media player for consistent experience
- **Volume Control**: Adjustable music levels with fade transitions
- **Multiple Playlists**: Curated classical, baroque, and piano collections

### 📊 Analytics & Tracking

- **Session Logging**: Automatic tracking of all timer sessions
- **Productivity Insights**: Detailed analytics with scoring and trend analysis
- **Export Capabilities**: CSV export for external analysis
- **Visual Charts**: Beautiful graphs showing productivity patterns over time

### 🔔 Smart Notifications

- **Cross-Platform Notifications**: Native desktop notifications on all platforms
- **Early Warnings**: Configurable alerts before session completion
- **Motivational Messages**: Encouraging notifications to maintain momentum
- **Multiple Notification Types**: Visual, audio, and system tray integration

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **MPV Media Player** (for music functionality)

### Installation

1. **Clone or download the project**:

   ```bash
   git clone https://github.com/yourusername/ultimate-focus-timer.git
   cd ultimate-focus-timer
   ```

2. **Set up virtual environment** (recommended):

   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run automated setup**:

   ```bash
   python setup.py
   ```

5. **Launch the application**:

   ```bash
   python main.py
   ```

### Quick Launch Options

```bash
# Interactive launcher menu (default)
python main.py

# Direct GUI launch
python main.py --gui

# Console mode
python main.py --console

# Analytics dashboard
python main.py --dashboard

# Quick 25-minute Pomodoro session
python main.py --pomodoro

# Custom work session (30 minutes)
python main.py --work 30

# Help and system information
python main.py --help
python main.py --info
```

## 🖥️ System Requirements

### Supported Platforms

- **Windows 10/11**
- **macOS 10.14+**
- **Linux** (Ubuntu, Debian, Fedora, Arch)

### Dependencies

- **Python 3.8+** (3.10+ recommended)
- **MPV Media Player** (auto-installed by setup script)
- **Python packages** (automatically installed):
  - PyYAML, matplotlib, pandas, seaborn
  - plyer, psutil, rich, click

## 📁 Project Structure

```text
ultimate-focus-timer/
├── main.py                 # Ultimate launcher with all functionality
├── setup.py               # Cross-platform setup and configuration
├── requirements.txt       # Python dependencies
├── config.yml             # User configuration file
├── 
├── core/                  # Core application modules
│   ├── config_manager.py  # Configuration management
│   ├── session_manager.py # Timer session logic
│   ├── music_controller.py# Music playback control
│   └── notification_manager.py # Cross-platform notifications
├── 
├── interfaces/            # User interfaces
│   ├── focus_gui.py       # GUI application
│   ├── focus_console.py   # Console interface
│   ├── dashboard.py       # Analytics dashboard
│   └── cli.py            # CLI utilities
├── 
├── data/                  # Application data
│   ├── focus.db          # Session database
│   ├── log/              # Application logs
│   └── exports/          # Data exports
├── 
├── music/                # Music files and playlists
├── static/               # Static assets (sounds, icons)
└── docs/                # Documentation
```

## ⚙️ Configuration

The application uses a YAML configuration file (`config.yml`) for customization:

### Session Settings

```yaml
work_mins: 25              # Work session duration
short_break_mins: 5        # Short break duration  
long_break_mins: 15        # Long break duration
long_break_interval: 4     # Sessions before long break
```

### Music Settings

```yaml
classical_music: true           # Enable background music
classical_music_volume: 70      # Music volume (0-100)
fade_music_transitions: true    # Smooth volume transitions
pause_music_on_break: true      # Auto-pause during breaks
```

### Notification Settings

```yaml
desktop_notifications: true     # Enable desktop notifications
notify_early_warning: 2         # Minutes before session end
motivational_messages: true     # Show encouraging messages
notification_priority: normal   # Notification priority level
```

### Interface Settings

```yaml
dark_theme: true               # Use dark theme
accent_color: "#00ff00"        # UI accent color
animated_transitions: true     # Enable animations
show_progress_bar: true        # Show progress indicators
```

## 🎵 Music Setup

### Automatic Setup

The setup script will automatically install MPV and configure music:

```bash
python setup.py
```

### Manual MPV Installation

**Windows:**

```bash
# Using Chocolatey
choco install mpv

# Using Winget  
winget install mpv
```

**macOS:**

```bash
# Using Homebrew
brew install mpv
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt install mpv

# Fedora
sudo dnf install mpv

# Arch Linux
sudo pacman -S mpv
```

### Custom Playlists

Add your own music by:

1. Creating `.m3u` playlist files in the `music/` directory
2. Updating `config.yml` with playlist paths
3. Supporting local files or online streams

## 📊 Analytics Dashboard

Access comprehensive productivity analytics through the dashboard:

```bash
python main.py --dashboard
```

### Available Metrics

- **Session Statistics**: Total sessions, duration, completion rates
- **Productivity Trends**: Daily, weekly, and monthly patterns
- **Break Analysis**: Break timing and effectiveness
- **Goal Tracking**: Progress towards productivity goals
- **Performance Scoring**: Productivity scoring algorithms

### Export Options

- **CSV Export**: Raw session data for external analysis
- **Report Generation**: Formatted productivity reports
- **Chart Export**: Save visualizations as images

## 🛠️ Troubleshooting

### Common Issues

**MPV Not Found**

```bash
# Check MPV installation
mpv --version

# Reinstall via setup script
python setup.py --reinstall-mpv
```

**Python Dependencies Missing**

```bash
# Check dependencies
python main.py --check-deps

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Virtual Environment Issues**

```bash
# Create new virtual environment
python -m venv .venv --clear

# Activate and reinstall
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**GUI Not Starting**

```bash
# Try console mode
python main.py --console

# Check system information
python main.py --info
```

### Debug Mode

Enable detailed logging:

```bash
python main.py --debug
```

## 🚀 Advanced Usage

### Command Line Interface

The application supports extensive CLI usage:

```bash
# System information
python main.py --info

# Dependency checking
python main.py --check-deps

# Configuration validation
python main.py --check-config

# Quick sessions
python main.py --work 45 --music classical
python main.py --break 10 --no-music

# Batch mode
python main.py --sessions 4 --work 25 --break 5
```

### Virtual Environment Workflow

For development and isolation:

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Run application
python main.py

# Deactivate when done
deactivate
```

### Desktop Integration

Create desktop shortcuts and system integration:

```bash
python setup.py --desktop-integration
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Set up development environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Make your changes
5. Run tests and submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Include docstrings for public methods
- Maintain cross-platform compatibility

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Francesco Cirillo** for the Pomodoro Technique
- **MPV Media Player** for excellent cross-platform audio support
- **Python Community** for the amazing ecosystem of libraries
- **Classical Music Communities** for curated playlists

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ultimate-focus-timer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ultimate-focus-timer/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/ultimate-focus-timer/wiki)

---

**Stay focused and productive! 🎯**

*Built with ❤️ for productivity enthusiasts worldwide*

---

**Stay focused and productive! 🎯**
