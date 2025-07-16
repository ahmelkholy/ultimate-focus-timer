@echo off
echo Building Focus Timer Application...
echo.

echo [1/4] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo.
echo [3/4] Building application...
python build.py
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying build...
if exist "dist\focus.exe" (
    echo SUCCESS: focus.exe created successfully!
    echo Location: %CD%\dist\focus.exe
    echo.
    echo Testing executable...
    echo.
    "dist\focus.exe" --version
    echo.
    echo Build completed successfully!
) else (
    echo ERROR: focus.exe was not created
    exit /b 1
)

echo.
echo You can now run the application with: dist\focus.exe
pause
