# Focus Timer Daemon Launcher (PowerShell)
# Usage: .\focus-daemon.ps1 -Action start|stop|status

param(
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "start"
)

$DAEMON_URL = "http://127.0.0.1:8765"
$PROJECT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$DAEMON_PID_FILE = Join-Path $PROJECT_DIR "daemon.pid"
$DAEMON_LOG = Join-Path $PROJECT_DIR "daemon.log"

function Test-DaemonRunning {
    if (-not (Test-Path $DAEMON_PID_FILE)) {
        return $false
    }
    $PID = Get-Content $DAEMON_PID_FILE -ErrorAction SilentlyContinue
    if ([string]::IsNullOrEmpty($PID)) {
        return $false
    }
    try {
        $proc = Get-Process -Id $PID -ErrorAction SilentlyContinue
        return $null -ne $proc
    } catch {
        return $false
    }
}

function Start-Daemon {
    Write-Host "[+] Starting Focus Timer daemon..." -ForegroundColor Green

    if (Test-DaemonRunning) {
        $PID = Get-Content $DAEMON_PID_FILE
        Write-Host "[!] Daemon already running (PID: $PID)" -ForegroundColor Yellow
        return
    }

    Push-Location $PROJECT_DIR
    try {
        # Start daemon process
        $proc = Start-Process -FilePath .\.venv\Scripts\python.exe `
                             -ArgumentList "-m", "src.daemon" `
                             -RedirectStandardOutput $DAEMON_LOG `
                             -RedirectStandardError $DAEMON_LOG `
                             -NoNewWindow `
                             -PassThru

        $proc.Id | Out-File $DAEMON_PID_FILE -NoNewline
        Start-Sleep -Seconds 2

        # Verify
        try {
            $response = Invoke-RestMethod -Uri "$DAEMON_URL/status" -Method Get -ErrorAction SilentlyContinue
            if ($response) {
                Write-Host "[OK] Daemon started on $DAEMON_URL (PID: $($proc.Id))" -ForegroundColor Green
                return
            }
        } catch {}

        Write-Host "[X] Daemon failed to start" -ForegroundColor Red
        Remove-Item $DAEMON_PID_FILE -ErrorAction SilentlyContinue
    } finally {
        Pop-Location
    }
}

function Stop-Daemon {
    Write-Host "[+] Stopping Focus Timer daemon..." -ForegroundColor Green

    if (-not (Test-Path $DAEMON_PID_FILE)) {
        Write-Host "[!] Daemon not running" -ForegroundColor Yellow
        return
    }

    $PID = Get-Content $DAEMON_PID_FILE -ErrorAction SilentlyContinue
    if (-not [string]::IsNullOrEmpty($PID)) {
        try {
            Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        } catch {}
    }

    Remove-Item $DAEMON_PID_FILE -ErrorAction SilentlyContinue
    Write-Host "[OK] Daemon stopped" -ForegroundColor Green
}

function Get-DaemonStatus {
    if (-not (Test-DaemonRunning)) {
        Write-Host "[!] Daemon not running" -ForegroundColor Yellow
        return
    }

    $PID = Get-Content $DAEMON_PID_FILE
    try {
        $response = Invoke-RestMethod -Uri "$DAEMON_URL/status" -Method Get -ErrorAction Stop
        Write-Host "[OK] Daemon running (PID: $PID)" -ForegroundColor Green
        Write-Host "  Phase: $($response.phase)" -ForegroundColor Cyan
        Write-Host "  Duration: $($response.phase_duration_minutes) min" -ForegroundColor Cyan
        Write-Host "  Remaining: $($response.remaining_seconds) sec" -ForegroundColor Cyan
    } catch {
        Write-Host "[!] Daemon not responding (stale PID file)" -ForegroundColor Yellow
        Remove-Item $DAEMON_PID_FILE -ErrorAction SilentlyContinue
    }
}

# Execute action
switch ($Action) {
    "start" { Start-Daemon }
    "stop" { Stop-Daemon }
    "status" { Get-DaemonStatus }
}
