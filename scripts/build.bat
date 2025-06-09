@echo off
REM Ultimate Focus Timer - Windows Build Script
REM Quick and easy building for Windows users

echo.
echo 🎯 Ultimate Focus Timer - Windows Build System
echo =============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Parse command line arguments
if "%1"=="" (
    echo Available commands:
    echo   setup     - Install all dependencies
    echo   build     - Build executable only
    echo   package   - Create distribution package
    echo   release   - Full release process
    echo   quick     - Quick build (dependencies + executable)
    echo.
    echo Usage: build.bat [command]
    pause
    exit /b 0
)

if "%1"=="setup" goto setup
if "%1"=="build" goto build
if "%1"=="package" goto package
if "%1"=="release" goto release
if "%1"=="quick" goto quick

echo ❌ Unknown command: %1
echo Run 'build.bat' for available commands
pause
exit /b 1

:setup
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-build.txt
echo ✅ Dependencies installed
goto end

:build
echo 🔨 Building executable...
python build_config.py build
echo ✅ Build completed
goto end

:package
echo 📦 Creating package...
python build_config.py all
echo ✅ Package created
goto end

:release
echo 🚀 Starting full release...
python release_manager.py full
echo ✅ Release completed
goto end

:quick
echo ⚡ Quick build process...
echo 📦 Installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
echo 🔨 Building executable...
python build_config.py all
echo ✅ Quick build completed!
echo 📁 Check the 'dist' folder for your executable
goto end

:end
echo.
echo 🎉 Process completed!
echo 📋 Next steps:
echo   - Check the 'dist' folder for built files
echo   - Test the executable before distribution
echo   - Use 'git push origin main --tags' to publish release
echo.
pause
