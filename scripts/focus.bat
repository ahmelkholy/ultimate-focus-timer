@echo off
REM Focus Timer Launcher Script for Windows Command Prompt
REM This batch file activates the virtual environment and launches Focus Timer

setlocal EnableDelayedExpansion

REM Focus Timer installation path
set FOCUS_PATH=c:\Users\ahm_e\AppData\Local\focus
set VENV_ACTIVATE=%FOCUS_PATH%\.venv\Scripts\activate.bat
set MAIN_SCRIPT=%FOCUS_PATH%\main.py

REM Check if installation exists
if not exist "%FOCUS_PATH%" (
    echo ❌ Focus Timer not found at: %FOCUS_PATH%
    echo 💡 Please ensure the Focus Timer is properly installed.
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_ACTIVATE%" (
    echo ❌ Virtual environment not found at: %VENV_ACTIVATE%
    echo 💡 Please run setup to create the virtual environment.
    exit /b 1
)

REM Save current directory
set ORIGINAL_DIR=%CD%

REM Change to Focus Timer directory
cd /d "%FOCUS_PATH%"

REM Activate virtual environment
call "%VENV_ACTIVATE%"

REM Parse command line arguments
if "%1"=="" (
    REM No parameters - show interactive launcher
    python main.py
) else if "%1"=="gui" (
    python main.py --gui
) else if "%1"=="console" (
    python main.py --console
) else if "%1"=="dashboard" (
    python main.py --dashboard
) else if "%1"=="stats" (
    python main.py --stats
) else if "%1"=="quick" (
    if "%2"=="" (
        python main.py --quick 25
    ) else (
        python main.py --quick %2
    )
) else if "%1"=="break" (
    if "%2"=="" (
        python main.py --break 5
    ) else (
        python main.py --break %2
    )
) else if "%1"=="check" (
    python main.py --check
) else if "%1"=="info" (
    python main.py --info
) else (
    echo ❌ Unknown mode: %1
    echo 📖 Available modes: gui, console, dashboard, quick [minutes], break [minutes], stats, check, info
    echo 📝 Examples:
    echo    focus
    echo    focus gui
    echo    focus quick 25
    echo    focus break 5
    echo    focus stats
)

REM Restore original directory
cd /d "%ORIGINAL_DIR%"

endlocal
