@echo off
title Enhanced Focus Terminal
cd /d "%~dp0"

echo.
echo ===================================
echo    Enhanced Focus Terminal
echo    With Classical Music Support
echo ===================================
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo PowerShell is required but not found.
    echo Please install PowerShell to use this application.
    pause
    exit /b 1
)

REM Run the launcher
powershell -ExecutionPolicy Bypass -File "launcher.ps1"

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to close.
    pause >nul
)
