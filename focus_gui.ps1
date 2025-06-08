# Enhanced Focus Timer with GUI
# A Windows Forms-based focus timer with classical music integration

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Global variables
$global:Timer = New-Object System.Windows.Forms.Timer
$global:SessionDuration = 0
$global:ElapsedSeconds = 0
$global:SessionType = "work"
$global:Config = @{}
$global:MusicProcess = $null

# Load configuration
function Load-Config {
    $configPath = "config.yml"
    $config = @{
        work_mins              = 25
        short_break_mins       = 5
        long_break_mins        = 15
        classical_music        = $true
        classical_music_volume = 30
        notify                 = $true
    }

    if (Test-Path $configPath) {
        $content = Get-Content $configPath
        foreach ($line in $content) {
            if ($line -match '^([^#:]+):\s*(.+)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()

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

# Music control functions
function Start-Music {
    if ($global:Config.classical_music) {
        $musicScript = "scripts\classical_music.ps1"
        if (Test-Path $musicScript) {
            try {
                Start-Process pwsh -ArgumentList "-ExecutionPolicy Bypass -File `"$musicScript`" -Action start -Volume $($global:Config.classical_music_volume)" -WindowStyle Hidden
                $script:lblMusicStatus.Text = "♪ Classical Music Playing"
                $script:lblMusicStatus.ForeColor = [System.Drawing.Color]::Green
            }
            catch {
                $script:lblMusicStatus.Text = "♪ Music Error"
                $script:lblMusicStatus.ForeColor = [System.Drawing.Color]::Red
            }
        }
    }
}

function Stop-Music {
    $musicScript = "scripts\classical_music.ps1"
    if (Test-Path $musicScript) {
        try {
            Start-Process pwsh -ArgumentList "-ExecutionPolicy Bypass -File `"$musicScript`" -Action stop" -WindowStyle Hidden
            $script:lblMusicStatus.Text = "♪ Music Stopped"
            $script:lblMusicStatus.ForeColor = [System.Drawing.Color]::Gray
        }
        catch {
            # Silent fail
        }
    }
}

# Session management
function Start-Session {
    param([string]$Type, [int]$Minutes)

    $global:SessionType = $Type
    $global:SessionDuration = $Minutes * 60
    $global:ElapsedSeconds = 0

    # Update UI
    $script:lblSessionType.Text = $Type.ToUpper() + " SESSION"
    $script:lblSessionType.ForeColor = if ($Type -eq "work") { [System.Drawing.Color]::DarkBlue } else { [System.Drawing.Color]::DarkGreen }

    $script:btnStart.Enabled = $false
    $script:btnStop.Enabled = $true
    $script:btnPause.Enabled = $true

    # Start music for work sessions
    if ($Type -eq "work") {
        Start-Music
    }

    # Start timer
    $global:Timer.Start()

    # Log session start
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "log\focus.log" -Value "$timestamp - Started $Type session ($Minutes minutes)"
}

function Stop-Session {
    $global:Timer.Stop()

    # Update UI
    $script:btnStart.Enabled = $true
    $script:btnStop.Enabled = $false
    $script:btnPause.Enabled = $false
    $script:lblTime.Text = "00:00"
    $script:progressBar.Value = 0

    # Stop music
    Stop-Music

    # Log session stop
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $completedMinutes = [math]::Round($global:ElapsedSeconds / 60, 1)
    Add-Content -Path "log\focus.log" -Value "$timestamp - Stopped $global:SessionType session (completed $completedMinutes minutes)"
}

function Complete-Session {
    $global:Timer.Stop()

    # Stop music
    Stop-Music

    # Show completion notification
    $title = "$($global:SessionType.ToUpper()) SESSION COMPLETE!"
    $message = "Great job! You completed a $($global:SessionDuration / 60) minute $global:SessionType session."

    [System.Windows.Forms.MessageBox]::Show($message, $title, [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)

    # Reset UI
    $script:btnStart.Enabled = $true
    $script:btnStop.Enabled = $false
    $script:btnPause.Enabled = $false
    $script:lblTime.Text = "COMPLETE!"
    $script:lblTime.ForeColor = [System.Drawing.Color]::Green
    $script:progressBar.Value = 100

    # Log completion
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "log\focus.log" -Value "$timestamp - Completed $global:SessionType session ($($global:SessionDuration / 60) minutes)"

    # Auto-suggest next session
    $nextSession = if ($global:SessionType -eq "work") { "short break" } else { "work" }
    $result = [System.Windows.Forms.MessageBox]::Show("Would you like to start a $nextSession session now?", "Next Session", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)

    if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
        $duration = if ($nextSession -eq "work") { $global:Config.work_mins } elseif ($nextSession -eq "short break") { $global:Config.short_break_mins } else { $global:Config.long_break_mins }
        Start-Session $nextSession.Replace(" ", "_") $duration
    }
}

# Timer tick event
function Timer-Tick {
    $global:ElapsedSeconds++

    $remaining = $global:SessionDuration - $global:ElapsedSeconds
    $minutes = [math]::Floor($remaining / 60)
    $seconds = $remaining % 60

    # Update time display
    $script:lblTime.Text = "${minutes}:$($seconds.ToString('00'))"
    $script:lblTime.ForeColor = if ($remaining -le 60) { [System.Drawing.Color]::Red } else { [System.Drawing.Color]::Black }

    # Update progress bar
    $progress = ($global:ElapsedSeconds / $global:SessionDuration) * 100
    $script:progressBar.Value = [math]::Min(100, [math]::Max(0, $progress))

    # Check if session is complete
    if ($global:ElapsedSeconds -ge $global:SessionDuration) {
        Complete-Session
    }

    # Early warning (2 minutes before end)
    if ($remaining -eq 120 -and $global:Config.notify) {
        [System.Windows.Forms.MessageBox]::Show("2 minutes remaining in your $global:SessionType session!", "Focus Timer", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
    }
}

# Create the main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Enhanced Focus Timer"
$form.Size = New-Object System.Drawing.Size(400, 500)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::WhiteSmoke

# Title label
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Text = "🎯 FOCUS TIMER"
$lblTitle.Font = New-Object System.Drawing.Font("Arial", 16, [System.Drawing.FontStyle]::Bold)
$lblTitle.ForeColor = [System.Drawing.Color]::DarkBlue
$lblTitle.Location = New-Object System.Drawing.Point(50, 20)
$lblTitle.Size = New-Object System.Drawing.Size(300, 30)
$lblTitle.TextAlign = "MiddleCenter"
$form.Controls.Add($lblTitle)

# Session type label
$script:lblSessionType = New-Object System.Windows.Forms.Label
$script:lblSessionType.Text = "READY TO START"
$script:lblSessionType.Font = New-Object System.Drawing.Font("Arial", 12, [System.Drawing.FontStyle]::Bold)
$script:lblSessionType.ForeColor = [System.Drawing.Color]::Gray
$script:lblSessionType.Location = New-Object System.Drawing.Point(50, 60)
$script:lblSessionType.Size = New-Object System.Drawing.Size(300, 25)
$script:lblSessionType.TextAlign = "MiddleCenter"
$form.Controls.Add($script:lblSessionType)

# Time display
$script:lblTime = New-Object System.Windows.Forms.Label
$script:lblTime.Text = "00:00"
$script:lblTime.Font = New-Object System.Drawing.Font("Courier New", 36, [System.Drawing.FontStyle]::Bold)
$script:lblTime.ForeColor = [System.Drawing.Color]::Black
$script:lblTime.Location = New-Object System.Drawing.Point(50, 100)
$script:lblTime.Size = New-Object System.Drawing.Size(300, 60)
$script:lblTime.TextAlign = "MiddleCenter"
$form.Controls.Add($script:lblTime)

# Progress bar
$script:progressBar = New-Object System.Windows.Forms.ProgressBar
$script:progressBar.Location = New-Object System.Drawing.Point(50, 180)
$script:progressBar.Size = New-Object System.Drawing.Size(300, 20)
$script:progressBar.Style = "Continuous"
$form.Controls.Add($script:progressBar)

# Work session button
$btnWork = New-Object System.Windows.Forms.Button
$btnWork.Text = "Work Session (25 min)"
$btnWork.Location = New-Object System.Drawing.Point(50, 220)
$btnWork.Size = New-Object System.Drawing.Size(140, 40)
$btnWork.BackColor = [System.Drawing.Color]::LightBlue
$btnWork.Add_Click({ Start-Session "work" $global:Config.work_mins })
$form.Controls.Add($btnWork)

# Short break button
$btnShortBreak = New-Object System.Windows.Forms.Button
$btnShortBreak.Text = "Short Break (5 min)"
$btnShortBreak.Location = New-Object System.Drawing.Point(210, 220)
$btnShortBreak.Size = New-Object System.Drawing.Size(140, 40)
$btnShortBreak.BackColor = [System.Drawing.Color]::LightGreen
$btnShortBreak.Add_Click({ Start-Session "short_break" $global:Config.short_break_mins })
$form.Controls.Add($btnShortBreak)

# Long break button
$btnLongBreak = New-Object System.Windows.Forms.Button
$btnLongBreak.Text = "Long Break (15 min)"
$btnLongBreak.Location = New-Object System.Drawing.Point(50, 270)
$btnLongBreak.Size = New-Object System.Drawing.Size(140, 40)
$btnLongBreak.BackColor = [System.Drawing.Color]::LightCoral
$btnLongBreak.Add_Click({ Start-Session "long_break" $global:Config.long_break_mins })
$form.Controls.Add($btnLongBreak)

# Custom session button
$btnCustom = New-Object System.Windows.Forms.Button
$btnCustom.Text = "Custom Session"
$btnCustom.Location = New-Object System.Drawing.Point(210, 270)
$btnCustom.Size = New-Object System.Drawing.Size(140, 40)
$btnCustom.BackColor = [System.Drawing.Color]::Khaki
$btnCustom.Add_Click({
        $minutes = [Microsoft.VisualBasic.Interaction]::InputBox("Enter session duration in minutes:", "Custom Session", "25")
        if ($minutes -match '^\d+$' -and [int]$minutes -gt 0) {
            Start-Session "custom" ([int]$minutes)
        }
    })
$form.Controls.Add($btnCustom)

# Control buttons
$script:btnStart = New-Object System.Windows.Forms.Button
$script:btnStart.Text = "▶ Start"
$script:btnStart.Location = New-Object System.Drawing.Point(50, 330)
$script:btnStart.Size = New-Object System.Drawing.Size(90, 30)
$script:btnStart.BackColor = [System.Drawing.Color]::LightGreen
$script:btnStart.Enabled = $false
$form.Controls.Add($script:btnStart)

$script:btnPause = New-Object System.Windows.Forms.Button
$script:btnPause.Text = "⏸ Pause"
$script:btnPause.Location = New-Object System.Drawing.Point(155, 330)
$script:btnPause.Size = New-Object System.Drawing.Size(90, 30)
$script:btnPause.BackColor = [System.Drawing.Color]::Yellow
$script:btnPause.Enabled = $false
$script:btnPause.Add_Click({
        if ($global:Timer.Enabled) {
            $global:Timer.Stop()
            $script:btnPause.Text = "▶ Resume"
            $script:btnPause.BackColor = [System.Drawing.Color]::LightGreen
        }
        else {
            $global:Timer.Start()
            $script:btnPause.Text = "⏸ Pause"
            $script:btnPause.BackColor = [System.Drawing.Color]::Yellow
        }
    })
$form.Controls.Add($script:btnPause)

$script:btnStop = New-Object System.Windows.Forms.Button
$script:btnStop.Text = "⏹ Stop"
$script:btnStop.Location = New-Object System.Drawing.Point(260, 330)
$script:btnStop.Size = New-Object System.Drawing.Size(90, 30)
$script:btnStop.BackColor = [System.Drawing.Color]::LightCoral
$script:btnStop.Enabled = $false
$script:btnStop.Add_Click({ Stop-Session })
$form.Controls.Add($script:btnStop)

# Music status label
$script:lblMusicStatus = New-Object System.Windows.Forms.Label
$script:lblMusicStatus.Text = "♪ Music Ready"
$script:lblMusicStatus.Font = New-Object System.Drawing.Font("Arial", 9)
$script:lblMusicStatus.ForeColor = [System.Drawing.Color]::Gray
$script:lblMusicStatus.Location = New-Object System.Drawing.Point(50, 375)
$script:lblMusicStatus.Size = New-Object System.Drawing.Size(200, 20)
$form.Controls.Add($script:lblMusicStatus)

# Statistics button
$btnStats = New-Object System.Windows.Forms.Button
$btnStats.Text = "📊 Stats"
$btnStats.Location = New-Object System.Drawing.Point(270, 375)
$btnStats.Size = New-Object System.Drawing.Size(80, 25)
$btnStats.Add_Click({
        $logPath = "log\focus.log"
        if (Test-Path $logPath) {
            $recent = Get-Content $logPath | Select-Object -Last 10
            $stats = $recent -join "`n"
            [System.Windows.Forms.MessageBox]::Show($stats, "Recent Sessions", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
        else {
            [System.Windows.Forms.MessageBox]::Show("No session history found.", "Statistics", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
    })
$form.Controls.Add($btnStats)

# Music control button
$btnMusicToggle = New-Object System.Windows.Forms.Button
$btnMusicToggle.Text = "🎵"
$btnMusicToggle.Location = New-Object System.Drawing.Point(50, 405)
$btnMusicToggle.Size = New-Object System.Drawing.Size(40, 25)
$btnMusicToggle.Add_Click({
        if ($global:Config.classical_music) {
            $musicScript = "scripts\classical_music.ps1"
            if (Test-Path $musicScript) {
                if ($script:lblMusicStatus.Text.Contains("Playing")) {
                    Stop-Music
                }
                else {
                    Start-Music
                }
            }
        }
    })
$form.Controls.Add($btnMusicToggle)

# Settings button
$btnSettings = New-Object System.Windows.Forms.Button
$btnSettings.Text = "⚙️ Settings"
$btnSettings.Location = New-Object System.Drawing.Point(270, 405)
$btnSettings.Size = New-Object System.Drawing.Size(80, 25)
$btnSettings.Add_Click({
        # Simple settings dialog
        $volume = [Microsoft.VisualBasic.Interaction]::InputBox("Enter music volume (0-100):", "Settings", $global:Config.classical_music_volume.ToString())
        if ($volume -match '^\d+$') {
            $global:Config.classical_music_volume = [math]::Min(100, [math]::Max(0, [int]$volume))
            [System.Windows.Forms.MessageBox]::Show("Volume set to $($global:Config.classical_music_volume)%", "Settings", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
    })
$form.Controls.Add($btnSettings)

# Initialize
$global:Config = Load-Config
$global:Timer.Interval = 1000
$global:Timer.Add_Tick({ Timer-Tick })

# Ensure log directory exists
if (!(Test-Path "log")) {
    New-Item -ItemType Directory -Path "log" -Force | Out-Null
}

# Add Visual Basic reference for InputBox
Add-Type -AssemblyName Microsoft.VisualBasic

# Show the form
Write-Host "Starting Enhanced Focus Timer GUI..." -ForegroundColor Green
[System.Windows.Forms.Application]::Run($form)

# Cleanup on exit
Stop-Music
Write-Host "Focus Timer closed. Stay productive!" -ForegroundColor Green
