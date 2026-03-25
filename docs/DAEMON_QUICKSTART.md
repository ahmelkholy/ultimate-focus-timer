# Quick Start - Daemon GUI Controls

**Updated**: 2026-03-25

---

## Now Working!

The daemon controls in the GUI are **fully operational**:

### GUI Usage

1. **Start the application**:
   ```bash
   python main.py --gui
   ```

2. **Daemon Control Frame** (at bottom of GUI):
   - **Status Label**: Shows real-time daemon status
     - Green dot: Daemon running
     - Red dot: Daemon stopped
     - Orange dot: Starting/Stopping
     - Question mark: Unknown state

   - **Start Daemon Button**: Click to start the Ultradian daemon
     - Disabled when daemon is already running
     - Shows "Starting..." feedback
     - Displays success/error message

   - **Stop Daemon Button**: Click to stop the daemon
     - Enabled only when daemon is running
     - Shows "Stopping..." feedback
     - Displays success/error message

3. **Status Updates**: The status label updates every 2 seconds automatically

---

## What the Daemon Does

The daemon runs a **FastAPI HTTP server** on `http://127.0.0.1:8765` that manages:

- **Ultradian Rhythm**: 90-minute focus cycles
  - 5 min: Ramp-up phase
  - 85 min: Deep work (peak focus)
  - 20 min: Neural rest (recovery)

- **HTTP API** for session control:
  - GET `/status` — Current session state
  - POST `/start` — Begin 90-minute session
  - POST `/stop` — End current session

- **Background Operation**: Runs non-blocking in background

---

## Fixed Issues

### ✓ Port Conflicts
Previously: "Only one usage of each socket address error"
Now: Automatic cleanup of stale processes

### ✓ Slow Startup Detection
Previously: Daemon would timeout before starting
Now: 7.5-second wait with proper health checks

### ✓ HTTP Request Failures
Previously: Proxy configuration blocked health checks
Now: Using urllib.request with fallback to requests

### ✓ Silent Failures
Previously: No error messages
Now: All errors logged to `daemon.log`

---

## Troubleshooting

### Daemon won't start
1. Check `daemon.log` for error messages
2. Kill any stale daemon processes:
   ```bash
   taskkill /F /IM python.exe
   ```
3. Verify port 8765 is free:
   ```bash
   netstat -ano | findstr 8765
   ```
4. Restart GUI and try again

### Daemon shows "Error" status
1. Check daemon.log
2. Restart daemon
3. Clear port and retry

### GUI not detecting daemon
1. Ensure firewall allows localhost:8765
2. Check that no proxy is blocking requests
3. Increase health check timeout if needed

---

## Advanced Usage

### Manual Daemon Control (Terminal)
```bash
# Start daemon
python -m src.daemon

# In another terminal, check status
curl http://127.0.0.1:8765/status

# Stop daemon
curl -X POST http://127.0.0.1:8765/stop
```

### View Daemon Logs
```bash
type daemon.log
```

### PowerShell Module
The PowerShell module also works with the daemon:
```powershell
focus gui                # Start GUI with daemon
focus-quick 25          # Start 25-min work with daemon
```

---

## Current Status

- **Daemon Manager**: Fully implemented
- **GUI Controls**: Integrated and tested
- **Status Monitoring**: Real-time updates working
- **Error Handling**: Improved with logging
- **Port Management**: Auto-cleanup of conflicts
- **Start/Stop**: Both operations successful

**Status: PRODUCTION READY** ✓

---

## What Changed This Session

1. **Fixed port binding conflicts** - Automatic stale process cleanup
2. **Improved startup detection** - Increased timeout and retry count
3. **Fixed proxy issues** - Using urllib for health checks
4. **Added error logging** - Daemon output captured to daemon.log
5. **Tested end-to-end** - GUI → Daemon → Status updates working

---

## All Systems Go! 🚀

You can now:
- ✓ Start daemon from GUI
- ✓ Monitor daemon status in real-time
- ✓ Stop daemon cleanly
- ✓ Get error messages if something fails
- ✓ Auto-recovery on port conflicts

Enjoy your Focus Timer with daemon support!

Generated: 2026-03-25
