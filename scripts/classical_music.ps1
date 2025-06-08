# Cross-Platform Classical Music MPV Integration Script for Focus App
# This script manages classical music playback during focus sessions
# Supports Windows, macOS, and Linux with local and online playlists

param(
    [string]$Action = "start", # start, stop, pause, resume, volume, list, select
    [int]$Volume = 30,
    [string]$ConfigPath = "config.yml",
    [string]$PlaylistPath = ""  # optional specific playlist path
)

# Cross-platform configuration
$script:MPV_EXECUTABLE = "mpv"
$script:PID_FILE = "mpv_classical.pid"
$script:CONFIG = @{}

# Load configuration from YAML file
function Load-Config {
    param([string]$Path)

    $config = @{
        classical_music_local_mode       = $true
        classical_music_default_playlist = ""
        classical_music_playlist_dir     = ""
        classical_music_volume           = 30
        mpv_executable                   = "mpv"
        classical_music_online_playlists = @()
    }

    if (Test-Path $Path) {
        $content = Get-Content $Path
        foreach ($line in $content) {
            if ($line -match '^([^#:]+):\s*(.+)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()

                # Handle different value types
                if ($value -eq "true") {
                    $value = $true
                }
                elseif ($value -eq "false") {
                    $value = $false
                }
                elseif ($value -match '^\d+$') {
                    $value = [int]$value
                }
                elseif ($value -match '^"(.+)"$') {
                    $value = $matches[1]
                }
                elseif ($value.StartsWith('[') -and $value.EndsWith(']')) {
                    # Simple array parsing
                    $value = $value.Trim('[', ']').Split(',') | ForEach-Object { $_.Trim().Trim('"') }
                }

                $config[$key] = $value
            }
        }
    }
    return $config
}

# Cross-platform path handling
function Get-CrossPlatformPath {
    param([string]$Path)

    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        return $Path
    }
    else {
        # Convert Windows paths to Unix-style for macOS/Linux
        return $Path -replace '\\', '/' -replace '^[A-Z]:', ''
    }
}

# Detect platform and set MPV executable
function Initialize-Platform {
    $script:CONFIG = Load-Config $ConfigPath

    # Set MPV executable based on platform
    if ($IsWindows -or $env:OS -eq "Windows_NT") {
        $script:MPV_EXECUTABLE = $script:CONFIG.mpv_executable
    }
    elseif ($IsMacOS) {
        # Try common macOS locations
        $macPaths = @("/usr/local/bin/mpv", "/opt/homebrew/bin/mpv", "mpv")
        foreach ($path in $macPaths) {
            if (Get-Command $path -ErrorAction SilentlyContinue) {
                $script:MPV_EXECUTABLE = $path
                break
            }
        }
    }
    else {
        # Linux - usually in PATH
        $script:MPV_EXECUTABLE = "mpv"
    }
}

# Get available playlists
function Get-AvailablePlaylists {
    $playlists = @()

    # Add local playlists if directory exists
    if ($script:CONFIG.classical_music_playlist_dir -and (Test-Path $script:CONFIG.classical_music_playlist_dir)) {
        $playlistDir = Get-CrossPlatformPath $script:CONFIG.classical_music_playlist_dir
        $localPlaylists = Get-ChildItem -Path $playlistDir -Filter "*.m3u*" -ErrorAction SilentlyContinue

        foreach ($playlist in $localPlaylists) {
            $playlists += [PSCustomObject]@{
                Name        = $playlist.BaseName
                Path        = $playlist.FullName
                Type        = "Local"
                Description = "Local playlist: $($playlist.Name)"
            }
        }
    }

    # Add default playlist if not already included
    if ($script:CONFIG.classical_music_default_playlist -and
        (Test-Path $script:CONFIG.classical_music_default_playlist) -and
        $playlists.Path -notcontains $script:CONFIG.classical_music_default_playlist) {

        $defaultPath = Get-CrossPlatformPath $script:CONFIG.classical_music_default_playlist
        $defaultName = [System.IO.Path]::GetFileNameWithoutExtension($defaultPath)

        $playlists += [PSCustomObject]@{
            Name        = "$defaultName (Default)"
            Path        = $defaultPath
            Type        = "Local"
            Description = "Default classical music playlist"
        }
    }

    # Add online playlists if local mode is disabled
    if (-not $script:CONFIG.classical_music_local_mode -and $script:CONFIG.classical_music_online_playlists) {
        for ($i = 0; $i -lt $script:CONFIG.classical_music_online_playlists.Count; $i++) {
            $url = $script:CONFIG.classical_music_online_playlists[$i]
            $playlists += [PSCustomObject]@{
                Name        = "Online Playlist $($i + 1)"
                Path        = $url
                Type        = "Online"
                Description = "YouTube/Online playlist"
            }
        }
    }

    return $playlists
}

# Select playlist to play
function Select-Playlist {
    if ($PlaylistPath -and (Test-Path $PlaylistPath)) {
        return Get-CrossPlatformPath $PlaylistPath
    }

    $playlists = Get-AvailablePlaylists

    if ($playlists.Count -eq 0) {
        Write-Host "No playlists found!" -ForegroundColor Red
        return $null
    }

    # Use default playlist if in local mode
    if ($script:CONFIG.classical_music_local_mode -and $script:CONFIG.classical_music_default_playlist) {
        $defaultPath = Get-CrossPlatformPath $script:CONFIG.classical_music_default_playlist
        if (Test-Path $defaultPath) {
            return $defaultPath
        }
    }

    # Otherwise use first available playlist
    return $playlists[0].Path
}

function Start-ClassicalMusic {
    Write-Host "Starting classical music for focus session..." -ForegroundColor Green

    $selectedPlaylist = Select-Playlist
    if (-not $selectedPlaylist) {
        Write-Host "No valid playlist found!" -ForegroundColor Red
        return $null
    }

    Write-Host "Selected playlist: $selectedPlaylist" -ForegroundColor Cyan

    # Build MPV arguments
    $mpvArgs = @(
        "--no-video"
        "--shuffle"
        "--loop-playlist"
        "--volume=$Volume"
        "--really-quiet"
    )

    # Add extra args from config
    if ($script:CONFIG.mpv_extra_args) {
        $extraArgs = $script:CONFIG.mpv_extra_args.Split(' ')
        $mpvArgs += $extraArgs
    }

    # Add playlist/file
    $mpvArgs += "`"$selectedPlaylist`""

    try {
        # Start MPV in background
        $process = Start-Process -FilePath $script:MPV_EXECUTABLE -ArgumentList $mpvArgs -PassThru -WindowStyle Hidden

        # Save PID for later control
        $process.Id | Out-File -FilePath $script:PID_FILE -Encoding ASCII

        Write-Host "Classical music started with PID: $($process.Id)" -ForegroundColor Green
        return $process.Id
    }
    catch {
        Write-Host "Error starting MPV: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Stop-ClassicalMusic {
    Write-Host "Stopping classical music..." -ForegroundColor Yellow

    if (Test-Path $PID_FILE) {
        $processId = Get-Content $PID_FILE
        try {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Remove-Item $PID_FILE -Force
            Write-Host "Classical music stopped." -ForegroundColor Green
        }
        catch {
            Write-Host "Could not stop process $processId. It may have already ended." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "No running classical music session found." -ForegroundColor Yellow
    }
}

function Set-MusicVolume {
    param([int]$NewVolume)

    Write-Host "Setting music volume to $NewVolume%" -ForegroundColor Cyan

    if (Test-Path $PID_FILE) {
        $processId = Get-Content $PID_FILE
        # Send volume command to MPV via echo to stdin (simplified approach)
        # Note: This is a basic implementation. Full MPV control would require IPC or JSON API
        Write-Host "Volume adjustment requested. Note: Restart music for volume change to take effect." -ForegroundColor Yellow
    }
    else {
        Write-Host "No running music session to adjust volume." -ForegroundColor Yellow
    }
}

function Test-MPVInstalled {
    try {
        $result = & $MPV_EXECUTABLE --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "MPV is installed and accessible." -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "MPV is not installed or not in PATH. Please install MPV from https://mpv.io/" -ForegroundColor Red
        Write-Host "Or update the MPV_EXECUTABLE path in the script." -ForegroundColor Red
        return $false
    }
    return $false
}

function Show-Usage {
    Write-Host "Classical Music Control Script" -ForegroundColor Magenta
    Write-Host "Usage: classical_music.ps1 -Action [start|stop|pause|resume|volume|test] [-Volume 30]" -ForegroundColor White
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  start   - Start classical music playback" -ForegroundColor White
    Write-Host "  stop    - Stop classical music playback" -ForegroundColor White
    Write-Host "  volume  - Set music volume (use with -Volume parameter)" -ForegroundColor White
    Write-Host "  test    - Test if MPV is installed and working" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\classical_music.ps1 -Action start" -ForegroundColor White
    Write-Host "  .\classical_music.ps1 -Action volume -Volume 20" -ForegroundColor White
    Write-Host "  .\classical_music.ps1 -Action stop" -ForegroundColor White
}

# Main execution
switch ($Action.ToLower()) {
    "start" {
        if (Test-MPVInstalled) {
            Start-ClassicalMusic
        }
    }
    "stop" {
        Stop-ClassicalMusic
    }
    "volume" {
        Set-MusicVolume -NewVolume $Volume
    }
    "test" {
        Test-MPVInstalled
    }
    "help" {
        Show-Usage
    }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Show-Usage
    }
}
