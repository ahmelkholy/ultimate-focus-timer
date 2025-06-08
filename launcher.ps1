# Focus Timer Launcher
# Choose between console and GUI versions

Write-Host "=== Enhanced Focus Timer ===" -ForegroundColor Magenta
Write-Host "🎯 Welcome to your productivity companion!" -ForegroundColor Cyan
Write-Host ""

# Check dependencies
function Test-Dependencies {
    $issues = @()

    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        $issues += "PowerShell 5.0 or higher required"
    }

    # Check MPV for music
    try {
        & mpv --version 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            $issues += "MPV not found (classical music will be disabled)"
        }
    }
    catch {
        $issues += "MPV not found (classical music will be disabled)"
    }

    # Check log directory
    if (!(Test-Path "log")) {
        New-Item -ItemType Directory -Path "log" -Force | Out-Null
        Write-Host "✓ Created log directory" -ForegroundColor Green
    }

    return $issues
}

# Show dependency issues
$issues = Test-Dependencies
if ($issues.Count -gt 0) {
    Write-Host "⚠️  Setup Issues:" -ForegroundColor Yellow
    foreach ($issue in $issues) {
        Write-Host "   • $issue" -ForegroundColor Yellow
    }
    Write-Host ""

    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "Run setup.ps1 to fix issues, then try again." -ForegroundColor Cyan
        exit
    }
}

# Show menu
Write-Host "Choose your focus experience:" -ForegroundColor White
Write-Host ""
Write-Host "1. 🖥️  GUI Timer (Recommended)" -ForegroundColor Cyan
Write-Host "   • Beautiful interface with progress bars" -ForegroundColor Gray
Write-Host "   • Visual notifications and controls" -ForegroundColor Gray
Write-Host "   • Built-in music controls" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 💻 Console Timer" -ForegroundColor Green
Write-Host "   • Lightweight terminal interface" -ForegroundColor Gray
Write-Host "   • Perfect for minimal setups" -ForegroundColor Gray
Write-Host "   • Command-line enthusiasts" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 🎵 Music Test" -ForegroundColor Magenta
Write-Host "   • Test classical music functionality" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 📊 Productivity Dashboard" -ForegroundColor Yellow
Write-Host "   • Detailed analytics and insights" -ForegroundColor Gray
Write-Host ""
Write-Host "5. 📈 View Statistics" -ForegroundColor Cyan
Write-Host "   • Show recent focus sessions" -ForegroundColor Gray
Write-Host ""
Write-Host "6. ⚙️  Setup & Configuration" -ForegroundColor Red
Write-Host "   • Initial setup and MPV installation" -ForegroundColor Gray
Write-Host ""

do {
    $choice = Read-Host "Enter your choice (1-6)"

    switch ($choice) {
        "1" {
            Write-Host "Starting GUI Focus Timer..." -ForegroundColor Green
            if (Test-Path "focus_gui.ps1") {
                & .\focus_gui.ps1
            }
            else {
                Write-Host "GUI script not found!" -ForegroundColor Red
            }
            break
        }
        "2" {
            Write-Host "Starting Console Focus Timer..." -ForegroundColor Green
            if (Test-Path "focus_manager.ps1") {
                & .\focus_manager.ps1
            }
            else {
                Write-Host "Console script not found!" -ForegroundColor Red
            }
            break
        }
        "3" {
            Write-Host "Testing classical music..." -ForegroundColor Magenta
            if (Test-Path "scripts\classical_music.ps1") {
                Write-Host "Testing MPV installation..." -ForegroundColor Cyan
                & .\scripts\classical_music.ps1 -Action test

                $test = Read-Host "Play test music for 10 seconds? (y/n)"
                if ($test -eq "y" -or $test -eq "Y") {
                    Write-Host "Starting test music..." -ForegroundColor Green
                    & .\scripts\classical_music.ps1 -Action start -Volume 20
                    Write-Host "Playing for 10 seconds..." -ForegroundColor Yellow
                    Start-Sleep 10
                    & .\scripts\classical_music.ps1 -Action stop
                    Write-Host "Test complete!" -ForegroundColor Green
                }
            }
            else {
                Write-Host "Music script not found!" -ForegroundColor Red
            }
            Read-Host "Press Enter to continue"
            continue
        }
        "4" {
            Write-Host "Opening Productivity Dashboard..." -ForegroundColor Yellow
            if (Test-Path "dashboard.ps1") {
                & .\dashboard.ps1
            }
            else {
                Write-Host "Dashboard script not found!" -ForegroundColor Red
            }
            Read-Host "Press Enter to continue"
            continue
        }
        "5" {
            Write-Host "=== Focus Session Statistics ===" -ForegroundColor Yellow
            $logPath = "log\focus.log"
            if (Test-Path $logPath) {
                $content = Get-Content $logPath
                Write-Host "Total sessions recorded: $($content.Count)" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "Recent sessions:" -ForegroundColor White
                $content | Select-Object -Last 10 | ForEach-Object {
                    Write-Host "  $_" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "No statistics available yet. Start some focus sessions!" -ForegroundColor Yellow
            }
            Read-Host "Press Enter to continue"
            continue
        }
        "6" {
            Write-Host "Running setup..." -ForegroundColor Red
            if (Test-Path "setup.ps1") {
                & .\setup.ps1
            }
            else {
                Write-Host "Setup script not found!" -ForegroundColor Red
            }
            Read-Host "Press Enter to continue"
            continue
        }
        default {
            Write-Host "Invalid choice. Please enter 1-6." -ForegroundColor Red
            continue
        }
    }
    break
} while ($true)

Write-Host ""
Write-Host "Thanks for using Enhanced Focus Timer! 🎯" -ForegroundColor Green
Write-Host "Stay focused and productive! 💪" -ForegroundColor Cyan
