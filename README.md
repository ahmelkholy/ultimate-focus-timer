# 🎯 Ultimate Focus Timer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Cross Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/ahmelkholy/ultimate-focus-timer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A science-backed, ultra-lightweight productivity timer implementing both traditional Pomodoro Technique and cutting-edge 90/20 Ultradian rhythm cycles. Features 40Hz cognitive enhancement, instant thought capture, VS Code integration, and zero-bloat architecture. Built with pure Python and modern async patterns.

## ✨ Key Features

### 🧠 Scientific Focus Technology
- **90/20 Ultradian Rhythm**: Research-backed 90-minute focus cycles with 20-minute recovery
- **40Hz Binaural Beats**: Gamma wave cognitive enhancement during deep work phases
- **Zeigarnik Offload System**: Instant thought capture (Ctrl+Shift+Space) to clear working memory
- **Distraction Blocking**: Automatic domain and process blocking during focus sessions

### 💻 Modern Development Integration
- **VS Code Extension**: One-click focus sessions with real-time status bar integration
- **Global CLI**: `focus start`, `focus status`, `focus stop` from any terminal
- **FastAPI Daemon**: Ultra-lightweight background service (~0% CPU when idle)
- **REST API**: Full programmatic control via HTTP endpoints

### 🎮 Traditional Features
- **Multiple Interfaces**: GUI, Console, Dashboard, and Interactive Launcher
- **Task Management**: Add, complete, and track tasks during focus sessions
- **Music Integration**: Classical music playback with cross-platform audio support
- **Analytics & Tracking**: Comprehensive session logging and productivity insights
- **Smart Notifications**: Cross-platform desktop notifications with early warnings
- **Cross-Platform**: Windows, macOS, and Linux support

## 💻 Quick Start

### Option 1: Daemon Mode (Recommended - Ultradian Rhythm)

**Start the daemon:**
```bash
python -m src.daemon
```

**Use from terminal:**
```bash
# Install global CLI
./scripts/install_global_cli.sh
source ~/.bashrc  # or ~/.zshrc

# Commands
focus start   # Start 90-minute Ultradian session
focus status  # Check progress
focus stop    # Stop session
```

**Use from VS Code:**
1. Install extension: `cd vscode-extension && npm install && npm run compile`
2. Press F5 to launch Extension Development Host
3. Click 🎯 Focus button in status bar

### Option 2: Traditional GUI (Pomodoro)

```bash
python main.py --gui
```

### Option 3: Console Mode

```bash
python main.py --console
```

### Option 4: Analytics Dashboard

```bash
python main.py --dashboard
```

## ☁️ Google Tasks Sync & Daemon Automation

1. Enable the **Google Tasks API** in your Google Cloud project and create an OAuth client (Desktop App).
2. Copy or download the OAuth client JSON once.
3. Connect Google Tasks in one of two ways:
   - **GUI**: open **Settings -> Tasks** and click **Connect Google Tasks**. If the OAuth JSON is missing, the app now opens the in-app setup helper so you can paste or browse the JSON and immediately continue into the browser sign-in flow.
   - **CLI**: run `focus --connect-tasks --google-credentials PATH_TO_CLIENT_JSON` or `python main.py --connect-tasks --google-credentials PATH_TO_CLIENT_JSON`.
4. After connecting, pick the Google task list in **Settings -> Tasks** or set `google_task_list_id` in `config.yml` (defaults to the primary list).
5. Incomplete tasks now carry forward automatically instead of disappearing on a new day, and Google sync no longer pulls only "today" tasks.
6. Press `Ctrl+S` in the GUI to force a sync. Failed updates are queued in `data/sync_queue.json` and retried with backoff.
7. The GUI auto-starts the FastAPI daemon in the background with no daemon controls shown in the main window. On Windows it is launched hidden, and the GUI stops the daemon instance it started when the app closes.

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Installation and usage for all modes
- **[Architecture Documentation](ARCHITECTURE.md)** - Technical details and API reference
- **[Complete Documentation](docs/README.md)** - Full user guide and features
- **[Virtual Environment Setup](docs/VENV_SETUP.md)** - Detailed environment configuration
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](docs/CHANGELOG.md)** - Version history and updates

## 🛠️ System Requirements

### For Daemon Mode (Ultradian Rhythm)
- **Python 3.8+** (Python 3.10+ recommended)
- **PortAudio** (for 40Hz binaural beats)
- **FastAPI & Uvicorn** (async web framework)
- **Optional**: VS Code for extension integration

### For Traditional Mode (Pomodoro GUI)
- **Python 3.8+** (Python 3.10+ recommended)
- **MPV Media Player** (auto-installed by setup script)
- **Tkinter** (usually included with Python)
- **Supported Platforms**: Windows 10/11, macOS 10.14+, Linux

## 📦 Installation

### Option 1: Daemon Mode Setup (Ultradian + VS Code)

```bash
# Clone repository
git clone https://github.com/ahmelkholy/ultimate-focus-timer.git
cd ultimate-focus-timer

# Install Python dependencies
pip install -r requirements.txt

# Install system audio library
# macOS
brew install portaudio

# Ubuntu/Debian
sudo apt-get install libportaudio2 python3-tk

# Fedora
sudo dnf install portaudio

# Install global CLI
./scripts/install_global_cli.sh
source ~/.bashrc  # or ~/.zshrc

# Install VS Code extension (optional)
cd vscode-extension
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host

# Optional: start daemon manually for debugging
python -m src.daemon

# Test it
focus start
```

### Option 2: Traditional GUI Setup (Pomodoro)

```bash
# Clone repository
git clone https://github.com/ahmelkholy/ultimate-focus-timer.git
cd ultimate-focus-timer

# Install dependencies
pip install -r requirements.txt

# Run setup (installs MPV)
python setup.py

# Launch GUI
python main.py --gui
```

## 🧬 Architecture

### Consolidated Module Structure

The codebase has been streamlined from 20 files to 11 core files (45% reduction):

**Core Modules:**
- `src/core.py` - Business logic (ConfigManager, SessionManager, TaskManager)
- `src/system.py` - System integration (Audio, Notifications, Paths, Hotkeys, Tray)
- `src/daemon.py` - FastAPI daemon with Ultradian state machine
- `src/audio_controller.py` - 40Hz binaural beat generator
- `src/zeigarnik_manager.py` - Global hotkey for thought capture

**UI Modules:**
- `src/focus_gui.py` - Tkinter GUI interface
- `src/focus_console.py` - Console interface
- `src/dashboard.py` - Analytics dashboard
- `src/cli.py` - Rich terminal CLI

**Integration:**
- `vscode-extension/` - TypeScript VS Code extension
- `scripts/focus` - Global CLI wrapper

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## 🧠 Scientific Foundation

### Ultradian Rhythm (90/20 Cycle)

Based on Nathaniel Kleitman's research on human alertness cycles:

1. **RAMP_UP (5 minutes)** - Gradual cognitive engagement
2. **DEEP_WORK (85 minutes)** - Peak performance with 40Hz enhancement
3. **NEURAL_REST (20 minutes)** - Complete mental recovery

### 40Hz Gamma Wave Enhancement

Research shows 40Hz stimulation:
- Enhances cognitive performance and memory consolidation
- Increases neural synchronization in prefrontal cortex
- Improves focus and information processing speed

Implementation: Real-time binaural beat generation (200 Hz left, 240 Hz right = 40 Hz perceived difference)

### Zeigarnik Effect Management

The Zeigarnik Effect states that incomplete tasks occupy working memory. Our solution:
- **Global Hotkey**: Ctrl+Shift+Space triggers instant capture
- **Zero-Friction**: Pop-up dialog with immediate save
- **Brain Dump**: Appends to timestamped markdown file
- **Result**: Clear working memory, maintain flow state

## 🎯 Usage Modes Comparison

| Feature | Daemon Mode | Traditional GUI |
|---------|-------------|-----------------|
| Session Length | 90 minutes (Ultradian) | 25 minutes (Pomodoro) |
| Cognitive Enhancement | 40Hz binaural beats | Classical music |
| Integration | VS Code + Global CLI | Standalone app |
| Resource Usage | ~0% CPU idle | Higher (GUI rendering) |
| Distraction Blocking | Automatic | Manual |
| Thought Capture | Ctrl+Shift+Space hotkey | Manual task entry |
| Best For | Deep work, coding | General productivity |

## ⚙️ Configuration

Edit `config.yml` to customize:

```yaml
# Traditional Pomodoro settings (for GUI/Console mode)
work_mins: 25
short_break_mins: 5
long_break_mins: 15

# Ultradian settings (for Daemon mode)
ultradian:
  ramp_up_minutes: 5
  deep_work_minutes: 85
  neural_rest_minutes: 20

# Audio settings
audio:
  enabled: true
  binaural_beat_volume: 0.15  # For daemon mode
  classical_music: true        # For traditional mode
  classical_music_volume: 70

# Distraction blocking (daemon mode)
distraction_blocking:
  enabled: true
  blocked_domains:
    - reddit.com
    - twitter.com
    - facebook.com
    - youtube.com
  blocked_processes:
    - slack
    - discord

# Notifications
notify_session_start: true
notify_session_complete: true
notify_early_warning: true
early_warning_minutes: 5

# Interface settings (traditional mode)
dark_theme: true
accent_color: "#00ff00"
animated_transitions: true
```

## 🔌 REST API Reference

The daemon exposes a simple REST API on `http://127.0.0.1:8765`:

### Endpoints

**GET /** - Health check
```json
{"status": "online", "name": "Ultimate Focus Timer Daemon", "version": "3.0.0"}
```

**POST /start** - Start Ultradian session
```bash
curl -X POST http://127.0.0.1:8765/start \
  -H "Content-Type: application/json" \
  -d '{"enable_audio": true, "enable_blocking": true}'
```

**GET /status** - Check session status
```json
{
  "phase": "deep_work",
  "phase_duration_minutes": 85,
  "remaining_seconds": 4800,
  "distraction_blocking_active": true,
  "audio_active": true
}
```

**POST /stop** - Stop current session
```bash
curl -X POST http://127.0.0.1:8765/stop
```

## 🔥 What's New in Version 3.0

### Zero-Bloat Scientific Upgrade
- **FastAPI Daemon**: Ultra-lightweight background service architecture
- **Ultradian Rhythm**: 90/20 cycle based on sleep research (5m + 85m + 20m)
- **40Hz Binaural Beats**: Real-time audio generation for cognitive enhancement
- **Zeigarnik Offload**: Global hotkey (Ctrl+Shift+Space) for instant thought capture
- **VS Code Extension**: Seamless IDE integration with status bar
- **Global CLI**: `focus` command available system-wide

### Codebase Consolidation
- **45% File Reduction**: 20 files → 11 core modules
- **Cleaner Architecture**: core.py, system.py, daemon.py structure
- **Better Maintainability**: Consolidated imports and dependencies
- **Faster Startup**: Reduced initialization overhead

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Francesco Cirillo** for the Pomodoro Technique
- **Nathaniel Kleitman** for Ultradian rhythm research
- **MPV Media Player** for excellent cross-platform audio support
- **FastAPI** for the modern async web framework
- **Python Community** for the amazing ecosystem

---

**Stay focused and productive!**

*Science-backed focus technology for developers*
