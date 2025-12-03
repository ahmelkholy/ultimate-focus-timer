#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch Focus Timer in background (detached from terminal)
.DESCRIPTION
    Starts the Focus Timer GUI as a background process that continues
    running even after closing the terminal.
.EXAMPLE
    focus-bg
    focus-bg gui
#>

param(
    [string]$Mode = "gui"
)

$FOCUS_PATH = "c:\Users\ahm_e\AppData\Local\focus"
$PYTHON = "$FOCUS_PATH\.venv\Scripts\python.exe"
$MAIN_SCRIPT = "$FOCUS_PATH\main.py"

if (-not (Test-Path $PYTHON)) {
    Write-Host "❌ Python not found in virtual environment" -ForegroundColor Red
    exit 1
}

# Build arguments
$pyArgs = @("`"$MAIN_SCRIPT`"")
if ($Mode -eq "gui" -or $Mode -eq "") {
    $pyArgs += "--gui"
} elseif ($Mode -eq "dashboard") {
    $pyArgs += "--dashboard"
} else {
    $pyArgs += "--$Mode"
}

# Start detached process (GUI will show, terminal returns immediately)
Start-Process -FilePath $PYTHON -ArgumentList $pyArgs -WorkingDirectory $FOCUS_PATH

Write-Host "✅ Focus Timer started in background" -ForegroundColor Green
