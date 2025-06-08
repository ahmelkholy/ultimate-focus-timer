#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Focus Timer Launcher Script for PowerShell
.DESCRIPTION
    This script activates the virtual environment and launches the Focus Timer
    from anywhere on your system.
.PARAMETER Mode
    Launch mode: gui, console, dashboard, quick, break, stats
.PARAMETER Duration
    Duration in minutes for quick sessions
.EXAMPLE
    focus
    focus gui
    focus quick 25
    focus break 5
    focus stats
#>

param(
    [string]$Mode = "",
    [int]$Duration = 0
)

# Focus Timer installation path
$FOCUS_PATH = "c:\Users\ahm_e\AppData\Local\focus"
$VENV_ACTIVATE = "$FOCUS_PATH\.venv\Scripts\Activate.ps1"
$MAIN_SCRIPT = "$FOCUS_PATH\main.py"

# Check if installation exists
if (-not (Test-Path $FOCUS_PATH)) {
    Write-Host "❌ Focus Timer not found at: $FOCUS_PATH" -ForegroundColor Red
    Write-Host "💡 Please ensure the Focus Timer is properly installed." -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path $VENV_ACTIVATE)) {
    Write-Host "❌ Virtual environment not found at: $VENV_ACTIVATE" -ForegroundColor Red
    Write-Host "💡 Please run setup to create the virtual environment." -ForegroundColor Yellow
    exit 1
}

# Save current location
$originalLocation = Get-Location

try {
    # Change to Focus Timer directory
    Set-Location $FOCUS_PATH

    # Activate virtual environment
    & $VENV_ACTIVATE

    # Determine command based on parameters
    if ($Mode -eq "") {
        # No parameters - show interactive launcher
        python main.py
    }
    elseif ($Mode -eq "gui") {
        python main.py --gui
    }
    elseif ($Mode -eq "console") {
        python main.py --console
    }
    elseif ($Mode -eq "dashboard") {
        python main.py --dashboard
    }
    elseif ($Mode -eq "stats") {
        python main.py --stats
    }
    elseif ($Mode -eq "quick") {
        if ($Duration -gt 0) {
            python main.py --quick $Duration
        } else {
            python main.py --quick 25  # Default 25 minutes
        }
    }
    elseif ($Mode -eq "break") {
        if ($Duration -gt 0) {
            python main.py --break $Duration
        } else {
            python main.py --break 5   # Default 5 minutes
        }
    }
    elseif ($Mode -eq "check") {
        python main.py --check
    }
    elseif ($Mode -eq "info") {
        python main.py --info
    }
    else {
        Write-Host "❌ Unknown mode: $Mode" -ForegroundColor Red
        Write-Host "📖 Available modes: gui, console, dashboard, quick [minutes], break [minutes], stats, check, info" -ForegroundColor Yellow
        Write-Host "📝 Examples:" -ForegroundColor Cyan
        Write-Host "   focus" -ForegroundColor White
        Write-Host "   focus gui" -ForegroundColor White
        Write-Host "   focus quick 25" -ForegroundColor White
        Write-Host "   focus break 5" -ForegroundColor White
        Write-Host "   focus stats" -ForegroundColor White
    }
}
catch {
    Write-Host "❌ Error launching Focus Timer: $_" -ForegroundColor Red
}
finally {
    # Restore original location
    Set-Location $originalLocation
}
