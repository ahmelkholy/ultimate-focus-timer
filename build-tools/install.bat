@echo off
echo Ultimate Focus Timer - Windows Installer
echo ========================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Run setup
echo Running setup...
python setup.py

echo.
echo Installation completed!
echo Run 'UltimateFocusTimer.exe' to start the application
pause
