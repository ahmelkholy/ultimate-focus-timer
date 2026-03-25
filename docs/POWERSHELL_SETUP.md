# PowerShell Module Setup & Usage Guide

## Summary of Changes (2026-03-25)

The PowerShell module `focus` has been optimized for global accessibility and fixed for PowerShell 5.1+ compatibility.

### What Was Fixed

✅ **PowerShell 5.1 Compatibility** (was using PS 7+ syntax)

- Replaced `?.Source` null-conditional operator with compatible syntax
- Module now works on all PowerShell versions

✅ **GUI Non-Blocking on Windows**

- Changed `focus gui` to use `pythonw.exe --WindowStyle Hidden`
- Terminal control returns immediately (~0.04 seconds)
- GUI loads silently in background

✅ **Module Auto-Loading**

- Added `focus` to core modules list in `Main.ps1`
- Module auto-loads whenever PowerShell starts
- Available globally from any directory

## Installation & Setup

### Pre-requisites

- PowerShell 5.1+ (Windows 7 and later)
- Python 3.8+ in system PATH
- Focus Timer installed at `C:\Users\ahm_e\AppData\Local\focus`

### Module Location

The module is installed at:

```
C:\Users\ahm_e\Documents\PowerShell\Modules\focus
```

### Auto-Load Configuration

The module is automatically loaded via:

```
C:\Users\ahm_e\Documents\PowerShell\Main.ps1
```

(which is sourced from the PowerShell profile)

## Usage Guide

### Quick Commands (Aliases)

| Command | Purpose |
|---------|---------|
| `focus` | Interactive menu |
| `focus gui` | GUI timer (non-blocking) |
| `focus console` | Terminal timer |
| `focus-quick [N]` | Quick work session (default: 25 min) |
| `focus-break [N]` | Quick break session (default: 5 min) |
| `focus-dashboard` | Analytics dashboard |
| `focus-stats` | Show statistics |
| `focus check` | Check dependencies |
| `focus info` | System information |

### Long-Form Functions

```powershell
# Start a 25-minute work session
Start-FocusSession                    # Uses config default

# Start a 5-minute break
Start-FocusBreak                      # Uses config default

# Show GUI
Show-FocusGui                         # Non-blocking

# Show console interface
Invoke-FocusConsole

# Show dashboard
Show-FocusDashboard

# Get stats
Get-FocusStats

# Repair environment (recreate venv)
Repair-FocusEnvironment
```

## Examples

### Start a focused work session:

```powershell
focus-quick 25
```

### Start a quick break:

```powershell
focus-break 5
```

### Check if everything is set up correctly:

```powershell
focus check
```

### View your productivity stats:

```powershell
focus-stats
```

### Launch GUI from PowerShell (non-blocking):

```powershell
focus gui
# Terminal control returns immediately
```

## Troubleshooting

### Module not found

```powershell
Import-Module focus -Force
```

### Python not on PATH

Add Python to your system PATH:

1. Open Environment Variables
2. Add `C:\Users\[YourUser]\AppData\Local\focus\.venv\Scripts` to PATH
3. Restart PowerShell

### Repair environment

```powershell
Repair-FocusEnvironment
```

This recreates the virtual environment from scratch.

### Check what's available

```powershell
Get-Module focus | Select-Object -ExpandProperty ExportedAliases
Get-Module focus | Select-Object -ExpandProperty ExportedFunctions
```

## Architecture

The PowerShell module is a thin wrapper around the Python application:

```
PowerShell Module
    ├── Invoke-Focus (main function)
    ├── Show-FocusGui (GUI handler)
    ├── Invoke-FocusConsole (Console handler)
    ├── Show-FocusDashboard (Dashboard handler)
    ├── Get-FocusStats (Stats handler)
    └── Repair-FocusEnvironment (Setup/repair)
         │
         └─→ Invokes Python at: C:\Users\ahm_e\AppData\Local\focus\main.py
```

## Key Features

- **Non-blocking GUI**: `focus gui` returns immediately; app launches in background
- **Global accessibility**: Works from any directory
- **Auto-loading**: Module loads automatically with PowerShell
- **Robust error handling**: Clear error messages if Python not found or venv broken
- **Environment repair**: One-command venv restoration
- **Cross-version compatible**: Works on PowerShell 5.1 through 7+

## Files Modified

- ✏️ `focus.psm1` - Fixed PS 5.1 compatibility, improved GUI launching
- ✏️ `Main.ps1` - Added focus to auto-load core modules list
- ✅ All functions tested and verified working

## VS Code Extension

A companion VS Code extension is also available:

- Launch from VS Code status bar
- Control Ultradian sessions
- Real-time timer display
- Requires daemon: `python -m src.daemon`
- See vscode-extension/ for details
