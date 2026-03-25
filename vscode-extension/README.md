# Ultimate Focus Timer - VS Code Extension

Instant access to Ultradian focus sessions (90-minute cycles) directly from your status bar.

## Features

- **Status Bar Button**: One-click access to start/stop focus sessions
- **Real-time Timer**: See remaining time directly in VS Code
- **Phase Indicators**: Visual feedback for current phase (Ramp Up, Deep Work, Neural Rest)
- **Command Palette**: Access all commands via Ctrl+Shift+P

## Requirements

- The Focus Timer daemon must be running: `python -m src.daemon`
- Python 3.8+ with required dependencies (fastapi, uvicorn, sounddevice, numpy)

## Installation

### From Source

1. Navigate to the extension directory:
   ```bash
   cd vscode-extension
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Compile TypeScript:
   ```bash
   npm run compile
   ```

4. Install the extension:
   - Open VS Code
   - Press F5 to launch Extension Development Host
   - Or: Copy the `vscode-extension` folder to `~/.vscode/extensions/`

## Usage

1. **Start the daemon** (in a separate terminal):
   ```bash
   python -m src.daemon
   ```

2. **Start a session**:
   - Click the "🎯 Focus" button in the status bar
   - Or: Ctrl+Shift+P → "Focus: Start Ultradian Session"

3. **Monitor progress**:
   - Status bar shows current phase and remaining time
   - Color coding:
     - 🔥 Ramp Up (5 min)
     - 🎯 Deep Work (85 min) - Red background
     - 🧘 Neural Rest (20 min) - Purple background

4. **Stop a session**:
   - Click the status bar during a session
   - Or: Ctrl+Shift+P → "Focus: Stop Session"

## Commands

- `Focus: Start Ultradian Session` - Start a new 90-minute Ultradian cycle
- `Focus: Stop Session` - Stop the current session
- `Focus: Show Status` - Display current session status

## Ultradian Rhythm (90/20 Protocol)

1. **Ramp Up (5 min)**: Transition into focus mode
2. **Deep Work (85 min)**: Peak cognitive performance
   - 40Hz binaural beats active
   - Distraction blocking enabled
3. **Neural Rest (20 min)**: Complete mental recovery
   - All blocking disabled
   - Recovery period

## Global Hotkey

**Ctrl+Shift+Space**: Quick brain dump (Zeigarnik offload)
- Opens instant text input
- Saves to `~/brain_dump.md`
- Clears working memory without breaking flow

## Development

```bash
npm run watch    # Watch mode for development
npm run compile  # One-time compilation
```

## License

MIT
