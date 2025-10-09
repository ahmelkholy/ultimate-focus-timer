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

if not exist "%MAIN_SCRIPT%" (
    echo ❌ Main launcher not found at: %MAIN_SCRIPT%
    echo 💡 Please verify the installation integrity.
    exit /b 1
)

REM Save current directory
set ORIGINAL_DIR=%CD%

REM Change to Focus Timer directory
cd /d "%FOCUS_PATH%"

REM Activate virtual environment
call "%VENV_ACTIVATE%"

REM Parse command line arguments
set MODE=%~1
set DURATION=%~2

if /I "%MODE%"=="" (
    REM No parameters - show interactive launcher
    python "%MAIN_SCRIPT%"
) else if /I "%MODE%"=="gui" (
    python "%MAIN_SCRIPT%" --gui
) else if /I "%MODE%"=="console" (
    python "%MAIN_SCRIPT%" --console
) else if /I "%MODE%"=="dashboard" (
    python "%MAIN_SCRIPT%" --dashboard
) else if /I "%MODE%"=="stats" (
    python "%MAIN_SCRIPT%" --stats
) else if /I "%MODE%"=="quick" (
    if "%DURATION%"=="" (
        python "%MAIN_SCRIPT%" --quick-session 25
    ) else (
        python "%MAIN_SCRIPT%" --quick-session %DURATION%
    )
) else if /I "%MODE%"=="break" (
    if "%DURATION%"=="" (
        python "%MAIN_SCRIPT%" --quick-break 5
    ) else (
        python "%MAIN_SCRIPT%" --quick-break %DURATION%
    )
) else if /I "%MODE%"=="check" (
    python "%MAIN_SCRIPT%" --check-deps
) else if /I "%MODE%"=="info" (
    python "%MAIN_SCRIPT%" --sys-info
) else if /I "%MODE%"=="interactive" (
    python "%MAIN_SCRIPT%" --interactive
) else (
    echo ❌ Unknown mode: %MODE%
    echo 📖 Available modes: gui, console, dashboard, quick [minutes], break [minutes], stats, check, info, interactive
    echo 📝 Examples:
    echo    focus
    echo    focus gui
    echo    focus quick 25
    echo    focus break 5
    echo    focus stats
    echo.
    echo 👉 Passing arguments directly to the app...
    python "%MAIN_SCRIPT%" %*
)

set EXITCODE=%ERRORLEVEL%

REM Restore original directory
cd /d "%ORIGINAL_DIR%"

endlocal & exit /b %EXITCODE%
