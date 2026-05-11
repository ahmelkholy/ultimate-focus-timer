# Ultimate Focus Timer - Quick Start Guide

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ahmelkholy/ultimate-focus-timer.git
   cd ultimate-focus-timer
   ```

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies (for audio):**

   ```bash
   # macOS
   brew install portaudio

   # Ubuntu/Debian
   sudo apt-get install libportaudio2 python3-tk

   # Fedora
   sudo dnf install portaudio
   ```

## Usage Options

### Option 1: GUI (Recommended)

**Start the GUI:**

```bash
python main.py --gui
```

The GUI is the lightest default path. The daemon is opt-in and only starts
automatically if `auto_start_daemon: true` is set in `config.yml`.

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

### Option 2: Traditional GUI (Original Pomodoro)

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

## Ultradian Session Flow

1. **RAMP_UP (5 minutes)**
   - Gradual transition into focus mode
   - No distractions blocked yet
   - Prepare your workspace

2. **DEEP_WORK (85 minutes)**
   - Peak cognitive performance
   - 40Hz binaural beats active (if enabled)
   - Distraction blocking active (if enabled)
   - Use Ctrl+Shift+Space for quick thoughts

3. **NEURAL_REST (20 minutes)**
   - Complete mental recovery
   - All blocking disabled
   - Take a walk, stretch, hydrate

4. **Repeat cycle as needed**

## Keyboard Shortcuts

### Global (Daemon Mode)

- `Ctrl+Shift+Space` - Quick brain dump (Zeigarnik offload)

### GUI Mode

- `T` - Add task
- `Space` - Start/Pause session
- `Ctrl+Q` - Quit
- `Ctrl+Alt+F` - Show window (global)
- `Ctrl+Alt+P` - Pause/Resume (global)

## Configuration

Edit `config.yml`:

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
  binaural_beat_volume: 0.15
  classical_music: true  # For traditional mode

# Distraction blocking
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
```

## Choosing Between Modes

### Use Daemon Mode If:

- You want science-backed 90-minute Ultradian cycles
- You want automatic distraction blocking
- You want 40Hz cognitive enhancement

### Use GUI Mode If:

- You prefer traditional 25-minute Pomodoro
- You want visual interface and statistics
- You want manual control over sessions
- You don't need background daemon

## Troubleshooting

### "Daemon not running" error

```bash
# Start the daemon manually when using CLI/API daemon features
python -m src.daemon
```

### "PortAudio library not found"

```bash
# Install system audio library (see Installation above)
# Then reinstall sounddevice
pip install --force-reinstall sounddevice
```

### "keyboard library not installed"

```bash
pip install keyboard

# On Linux, may require sudo for global hotkeys
sudo python -m src.daemon
```

### GUI won't start

```bash
# Check tkinter installation
python -c "import tkinter; print('OK')"

# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS (included by default)
# Windows (included by default)
```

## Documentation

- `ARCHITECTURE.md` - Detailed architecture documentation
- `docs/` - Additional documentation

## Support

- GitHub Issues: https://github.com/ahmelkholy/ultimate-focus-timer/issues
- Documentation: See docs/ folder

## License

MIT License
