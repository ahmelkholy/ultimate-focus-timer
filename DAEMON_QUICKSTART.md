# Quick Start - Auto-Managed Daemon

**Updated**: 2026-04-14

---

## Default behavior

The GUI now manages the daemon for you:

1. Start the app:

   ```bash
   python main.py --gui
   ```

   Or launch `focus.bat` / `focus.pyw` on Windows.

2. The app starts the FastAPI daemon automatically in the background.

3. The main GUI no longer shows daemon start/stop controls at the bottom.

4. On Windows the daemon is launched with a hidden Python process, so no extra terminal window should stay open for the daemon.

5. When the GUI closes, it stops the daemon process that this GUI instance started.

---

## What the daemon does

The daemon runs a **FastAPI HTTP server** on `http://127.0.0.1:8765` that manages:

- **Ultradian Rhythm**
  - 5 min: Ramp-up
  - 85 min: Deep work
  - 20 min: Neural rest

- **HTTP API**
  - `GET /status` — Current session state
  - `POST /start` — Begin a 90-minute session
  - `POST /stop` — End the current session

- **Background sync**
  - Periodic Google Tasks sync
  - Sync when the cycle enters Rest

---

## Manual mode (advanced only)

You only need to start the daemon manually when debugging or talking to the API directly:

```bash
python -m src.daemon
```

Then:

```bash
curl http://127.0.0.1:8765/status
curl -X POST http://127.0.0.1:8765/stop
```

---

## Troubleshooting

### The daemon did not start with the GUI

1. Check `daemon.log`
2. Make sure port `8765` is free
3. Restart the GUI

### A terminal window still appears on Windows

Start the GUI with one of these launchers instead of running the daemon directly:

```bash
python main.py --gui
focus.bat
```

### Need to inspect daemon output

```bash
type daemon.log
```
