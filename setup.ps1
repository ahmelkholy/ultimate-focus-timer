# Focus App Setup Script
# This script helps set up the enhanced focus terminal with MPV integration

Write-Host "=== Enhanced Focus Terminal Setup ===" -ForegroundColor Magenta

# Check if MPV is installed
function Test-MPVInstallation {
    try {
        $mpvVersion = & mpv --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ MPV is already installed" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ MPV is not installed" -ForegroundColor Red
        return $false
    }
}

# Install MPV using chocolatey or provide instructions
function Install-MPV {
    Write-Host "Installing MPV for classical music support..." -ForegroundColor Yellow

    # Check if chocolatey is available
    try {
        $chocoVersion = & choco --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installing MPV via Chocolatey..." -ForegroundColor Cyan
            & choco install mpv -y
            return
        }
    }
    catch {
        # Chocolatey not available
    }

    # Check if winget is available
    try {
        $wingetVersion = & winget --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Installing MPV via Winget..." -ForegroundColor Cyan
            & winget install mpv
            return
        }
    }
    catch {
        # Winget not available
    }

    # Provide manual installation instructions
    Write-Host "Please install MPV manually:" -ForegroundColor Yellow
    Write-Host "1. Visit https://mpv.io/installation/" -ForegroundColor White
    Write-Host "2. Download MPV for Windows" -ForegroundColor White
    Write-Host "3. Extract to a folder and add to PATH" -ForegroundColor White
    Write-Host "4. Or use: choco install mpv (if you have Chocolatey)" -ForegroundColor White
    Write-Host "5. Or use: winget install mpv (if you have Winget)" -ForegroundColor White
}

# Create necessary directories
function Initialize-Directories {
    Write-Host "Creating necessary directories..." -ForegroundColor Cyan

    $directories = @("scripts", "log", "static", "backups")
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "Created directory: $dir" -ForegroundColor Green
        }
    }
}

# Test classical music functionality
function Test-ClassicalMusic {
    Write-Host "Testing classical music functionality..." -ForegroundColor Cyan

    $musicScript = "scripts\classical_music.ps1"
    if (Test-Path $musicScript) {
        & $musicScript -Action test

        $testMusic = Read-Host "Would you like to test classical music playback? (y/n)"
        if ($testMusic -eq "y" -or $testMusic -eq "Y") {
            Write-Host "Starting test music (will stop in 10 seconds)..." -ForegroundColor Yellow
            & $musicScript -Action start -Volume 20
            Start-Sleep 10
            & $musicScript -Action stop
            Write-Host "Test completed!" -ForegroundColor Green
        }
    }
}

# Create a desktop shortcut
function Create-DesktopShortcut {
    $createShortcut = Read-Host "Create desktop shortcut for Focus Manager? (y/n)"
    if ($createShortcut -eq "y" -or $createShortcut -eq "Y") {
        try {
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\Enhanced Focus.lnk")
            $Shortcut.TargetPath = "powershell.exe"
            $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$PWD\focus_manager.ps1`""
            $Shortcut.WorkingDirectory = $PWD
            $Shortcut.IconLocation = "shell32.dll,21"  # Clock icon
            $Shortcut.Description = "Enhanced Focus Terminal with Classical Music"
            $Shortcut.Save()
            Write-Host "✓ Desktop shortcut created" -ForegroundColor Green
        }
        catch {
            Write-Host "✗ Could not create desktop shortcut" -ForegroundColor Red
        }
    }
}

# Show configuration summary
function Show-ConfigSummary {
    Write-Host "`n=== Configuration Summary ===" -ForegroundColor Magenta

    if (Test-Path "config.yml") {
        $configContent = Get-Content "config.yml"

        # Extract key settings
        $classicalMusic = ($configContent | Where-Object { $_ -match "classical_music:" } | Select-Object -First 1) -replace "classical_music:\s*", ""
        $musicVolume = ($configContent | Where-Object { $_ -match "classical_music_volume:" } | Select-Object -First 1) -replace "classical_music_volume:\s*", ""
        $workMins = ($configContent | Where-Object { $_ -match "work_mins:" } | Select-Object -First 1) -replace "work_mins:\s*", ""

        Write-Host "Classical Music Enabled: $classicalMusic" -ForegroundColor Cyan
        Write-Host "Music Volume: $musicVolume%" -ForegroundColor Cyan
        Write-Host "Work Session Duration: $workMins minutes" -ForegroundColor Cyan
    }

    Write-Host "`nAvailable Scripts:" -ForegroundColor Yellow
    Write-Host "• focus_manager.ps1 - Main focus session manager" -ForegroundColor White
    Write-Host "• scripts\classical_music.ps1 - Classical music control" -ForegroundColor White

    Write-Host "`nUsage:" -ForegroundColor Yellow
    Write-Host "Run: .\focus_manager.ps1" -ForegroundColor White
    Write-Host "Or use the desktop shortcut if created" -ForegroundColor White
}

# Main setup process
Write-Host "Starting setup process..." -ForegroundColor Cyan

# 1. Initialize directories
Initialize-Directories

# 2. Check and install MPV
if (!(Test-MPVInstallation)) {
    $installMpv = Read-Host "MPV is required for classical music. Install it now? (y/n)"
    if ($installMpv -eq "y" -or $installMpv -eq "Y") {
        Install-MPV
    }
}

# 3. Test functionality
if (Test-MPVInstallation) {
    Test-ClassicalMusic
}

# 4. Create shortcuts
Create-DesktopShortcut

# 5. Show summary
Show-ConfigSummary

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "Your enhanced focus terminal is ready to use." -ForegroundColor White
Write-Host "Run .\focus_manager.ps1 to start your first focus session." -ForegroundColor White
