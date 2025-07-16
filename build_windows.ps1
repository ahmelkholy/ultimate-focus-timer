# PowerShell build script for Focus Timer
Write-Host "Building Focus Timer Application..." -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

Write-Host ""
Write-Host "[3/4] Building application..." -ForegroundColor Yellow
python build.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[4/4] Verifying build..." -ForegroundColor Yellow
if (Test-Path "dist\focus.exe") {
    Write-Host "SUCCESS: focus.exe created successfully!" -ForegroundColor Green
    Write-Host "Location: $(Get-Location)\dist\focus.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host "Testing executable..." -ForegroundColor Yellow
    Write-Host ""
    & "dist\focus.exe" --version
    Write-Host ""
    Write-Host "Build completed successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: focus.exe was not created" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "You can now run the application with: dist\focus.exe" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
