# Enhanced Focus Session Manager
# Integrates classical music, notifications, and productivity tracking

param(
    [string]$SessionType = "work", # work, short_break, long_break
    [int]$Duration = 25, # session duration in minutes
    [string]$ConfigFile = "config.yml"
)

# Import configuration
function Read-Config {
    param([string]$Path)

    $config = @{}
    if (Test-Path $Path) {
        $content = Get-Content $Path
        foreach ($line in $content) {
            if ($line -match '^([^#:]+):\s*(.+)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()

                # Parse different value types
                if ($value -eq "true") { $value = $true }
                elseif ($value -eq "false") { $value = $false }
                elseif ($value -match '^\d+$') { $value = [int]$value }
                elseif ($value -match '^"(.+)"$') { $value = $matches[1] }

                $config[$key] = $value
            }
        }
    }
    return $config
}

function Start-FocusSession {
    param(
        [string]$Type,
        [int]$Minutes,
        [hashtable]$Config
    )

    Write-Host "=== Starting $Type Session ($Minutes minutes) ===" -ForegroundColor Magenta

    # Start classical music if enabled and it's a work session
    if ($Config.classical_music -and $Type -eq "work") {
        Write-Host "Starting classical music..." -ForegroundColor Green
        $musicScript = Join-Path $PSScriptRoot "classical_music.ps1"
        if (Test-Path $musicScript) {
            & $musicScript -Action start -Volume $Config.classical_music_volume
        }
    }

    # Display session info
    $endTime = (Get-Date).AddMinutes($Minutes)
    Write-Host "Session will end at: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Cyan

    # Session timer with progress updates
    $totalSeconds = $Minutes * 60
    $warningSeconds = ($Config.notify_early_warning ?? 2) * 60

    for ($i = 0; $i -lt $totalSeconds; $i++) {
        $remaining = $totalSeconds - $i
        $remainingMinutes = [math]::Floor($remaining / 60)
        $remainingSeconds = $remaining % 60

        # Progress bar
        $progress = ($i / $totalSeconds) * 100
        $timeString = "${remainingMinutes}:$($remainingSeconds.ToString('00'))"
        Write-Progress -Activity "$Type Session" -Status "Time remaining: $timeString" -PercentComplete $progress

        # Early warning notification
        if ($remaining -eq $warningSeconds -and $Config.notify_early_warning -gt 0) {
            Show-Notification "Focus Session" "$($Config.notify_early_warning) minutes remaining in $Type session" "Warning"
        }

        Start-Sleep 1
    }

    # Session completed
    Write-Progress -Activity "$Type Session" -Completed
    Write-Host "=== $Type Session Completed! ===" -ForegroundColor Green

    # Stop music if it was a work session
    if ($Config.classical_music -and $Type -eq "work" -and $Config.pause_music_on_break) {
        $musicScript = Join-Path $PSScriptRoot "classical_music.ps1"
        if (Test-Path $musicScript) {
            & $musicScript -Action stop
        }
    }

    # Show completion notification
    Show-Notification "Focus Session" "$Type session completed!" "Success"

    # Play completion sound
    if ($Config.notify_sound) {
        Play-NotificationSound $Type $Config
    }

    # Log session
    Log-Session $Type $Minutes $Config
}

function Show-Notification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "Info"
    )

    # Windows Toast Notification (requires Windows 10+)
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = $Title
        $notification.BalloonTipText = $Message
        $notification.Visible = $true
        $notification.ShowBalloonTip(5000)

        # Clean up
        Start-Sleep 6
        $notification.Dispose()
    }
    catch {
        # Fallback to console notification
        Write-Host "NOTIFICATION: $Title - $Message" -ForegroundColor Yellow
    }
}

function Play-NotificationSound {
    param(
        [string]$SessionType,
        [hashtable]$Config
    )

    $soundFile = ""
    switch ($SessionType) {
        "work" { $soundFile = "static/BellCongratulations.mp3" }
        "short_break" { $soundFile = "static/Beep.mp3" }
        "long_break" { $soundFile = "static/Correcto.mp3" }
    }

    if ($soundFile -and (Test-Path $soundFile)) {
        try {
            # Try to play with Windows Media Player
            $player = New-Object -ComObject WMPlayer.OCX
            $player.URL = (Resolve-Path $soundFile).Path
            $player.controls.play()
            Start-Sleep 2
        }
        catch {
            # Fallback to system beep
            [Console]::Beep(800, 200)
        }
    }
}

function Log-Session {
    param(
        [string]$Type,
        [int]$Minutes,
        [hashtable]$Config
    )

    $logFile = "log/focus.log"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp - $Type session completed - Duration: $Minutes minutes"

    # Ensure log directory exists
    $logDir = Split-Path $logFile -Parent
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    Add-Content -Path $logFile -Value $logEntry
}

function Show-SessionMenu {
    Write-Host "=== Enhanced Focus Session Manager ===" -ForegroundColor Magenta
    Write-Host "1. Start Work Session (25 min)" -ForegroundColor White
    Write-Host "2. Start Short Break (5 min)" -ForegroundColor White
    Write-Host "3. Start Long Break (15 min)" -ForegroundColor White
    Write-Host "4. Custom Session" -ForegroundColor White
    Write-Host "5. Test Classical Music" -ForegroundColor White
    Write-Host "6. View Statistics" -ForegroundColor White
    Write-Host "7. Exit" -ForegroundColor White
    Write-Host ""

    do {
        $choice = Read-Host "Select an option (1-7)"
        switch ($choice) {
            "1" { return @{Type = "work"; Minutes = 25 } }
            "2" { return @{Type = "short_break"; Minutes = 5 } }
            "3" { return @{Type = "long_break"; Minutes = 15 } }
            "4" {
                $customType = Read-Host "Enter session type (work/break)"
                $customMinutes = Read-Host "Enter duration in minutes"
                return @{Type = $customType; Minutes = [int]$customMinutes }
            }
            "5" {
                $musicScript = Join-Path $PSScriptRoot "classical_music.ps1"
                if (Test-Path $musicScript) {
                    & $musicScript -Action test
                    & $musicScript -Action start -Volume 20
                    Read-Host "Press Enter to stop test music"
                    & $musicScript -Action stop
                }
                continue
            }
            "6" {
                Show-Statistics
                continue
            }
            "7" { return $null }
            default {
                Write-Host "Invalid choice. Please select 1-7." -ForegroundColor Red
                continue
            }
        }
    } while ($true)
}

function Show-Statistics {
    $logFile = "log/focus.log"
    if (Test-Path $logFile) {
        Write-Host "=== Recent Focus Sessions ===" -ForegroundColor Cyan
        Get-Content $logFile | Select-Object -Last 10 | ForEach-Object {
            Write-Host $_ -ForegroundColor White
        }
    }
    else {
        Write-Host "No session history found." -ForegroundColor Yellow
    }
    Read-Host "Press Enter to continue"
}

# Main execution
$config = Read-Config $ConfigFile

# Show welcome message
Write-Host "Enhanced Focus Terminal" -ForegroundColor Magenta
Write-Host "Classical music integration enabled: $($config.classical_music)" -ForegroundColor Cyan

if ($SessionType -and $Duration) {
    # Direct session start (for programmatic use)
    Start-FocusSession -Type $SessionType -Minutes $Duration -Config $config
}
else {
    # Interactive mode
    while ($true) {
        $session = Show-SessionMenu
        if ($session) {
            Start-FocusSession -Type $session.Type -Minutes $session.Minutes -Config $config
        }
        else {
            break
        }
    }
}

Write-Host "Focus session ended. Stay productive!" -ForegroundColor Green
