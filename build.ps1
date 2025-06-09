# Ultimate Focus Timer - PowerShell Build Script
# Enhanced Windows build system with better error handling

param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "build", "package", "release", "quick", "test", "clean")]
    [string]$Command = "",

    [switch]$Force,
    [switch]$Verbose,
    [switch]$NoTest
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "🎯 $Title" -ForegroundColor Cyan
    Write-Host ("=" * ($Title.Length + 3)) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "📋 $Message" -ForegroundColor Blue
}

function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python found: $pythonVersion"
            return $true
        }
    }
    catch {
        Write-Error-Custom "Python is not installed or not in PATH"
        Write-Info "Please install Python 3.8+ from https://python.org"
        return $false
    }
    return $false
}

function Install-Dependencies {
    param([string]$RequirementsFile)

    Write-Info "Installing dependencies from $RequirementsFile..."

    try {
        python -m pip install --upgrade pip
        python -m pip install -r $RequirementsFile
        Write-Success "Dependencies from $RequirementsFile installed successfully"
        return $true
    }
    catch {
        Write-Error-Custom "Failed to install dependencies from $RequirementsFile"
        return $false
    }
}

function Invoke-Setup {
    Write-Header "Setting up Ultimate Focus Timer"

    if (-not (Test-PythonInstallation)) {
        return $false
    }

    # Install all dependencies
    $requirements = @("requirements.txt", "requirements-build.txt")

    foreach ($req in $requirements) {
        if (Test-Path $req) {
            if (-not (Install-Dependencies $req)) {
                return $false
            }
        }
        else {
            Write-Warning "Requirements file $req not found, skipping"
        }
    }

    # Run setup script
    Write-Info "Running setup script..."
    try {
        python setup.py install
        Write-Success "Setup completed successfully"
        return $true
    }
    catch {
        Write-Error-Custom "Setup script failed"
        return $false
    }
}

function Invoke-Build {
    Write-Header "Building Ultimate Focus Timer Executable"

    if (-not (Test-PythonInstallation)) {
        return $false
    }

    # Install build dependencies if needed
    if (-not (Test-Path "requirements-build.txt") -or $Force) {
        Install-Dependencies "requirements-build.txt"
    }

    Write-Info "Building executable..."
    try {
        python build_config.py build
        Write-Success "Executable built successfully"

        # Check if build artifacts exist
        if (Test-Path "dist") {
            $artifacts = Get-ChildItem "dist" -Name
            Write-Info "Build artifacts created:"
            foreach ($artifact in $artifacts) {
                Write-Host "  📁 $artifact"
            }
        }

        return $true
    }
    catch {
        Write-Error-Custom "Build failed"
        return $false
    }
}

function Invoke-Package {
    Write-Header "Creating Distribution Package"

    if (-not (Test-PythonInstallation)) {
        return $false
    }

    Write-Info "Creating complete package..."
    try {
        python build_config.py all
        Write-Success "Package created successfully"
        return $true
    }
    catch {
        Write-Error-Custom "Packaging failed"
        return $false
    }
}

function Invoke-Release {
    Write-Header "Full Release Process"

    if (-not (Test-PythonInstallation)) {
        return $false
    }

    # Run tests first (unless skipped)
    if (-not $NoTest) {
        Write-Info "Running tests before release..."
        try {
            python run_tests.py --unit --verbose
            Write-Success "Tests passed"
        }
        catch {
            Write-Warning "Tests failed, but continuing with release"
        }
    }

    Write-Info "Starting full release process..."
    try {
        python release_manager.py full
        Write-Success "Release process completed"

        Write-Info "Next steps:"
        Write-Host "  1. Test the built executable" -ForegroundColor Yellow
        Write-Host "  2. Review the release notes" -ForegroundColor Yellow
        Write-Host "  3. Push to GitHub: git push origin main --tags" -ForegroundColor Yellow

        return $true
    }
    catch {
        Write-Error-Custom "Release process failed"
        return $false
    }
}

function Invoke-QuickBuild {
    Write-Header "Quick Build Process"

    if (-not (Test-PythonInstallation)) {
        return $false
    }

    # Quick dependency check and install
    Write-Info "Installing build dependencies..."
    Install-Dependencies "requirements-build.txt"

    # Build
    Write-Info "Building executable..."
    try {
        python build_config.py all
        Write-Success "Quick build completed!"
        Write-Info "Check the 'dist' folder for your executable"
        return $true
    }
    catch {
        Write-Error-Custom "Quick build failed"
        return $false
    }
}

function Invoke-Test {
    Write-Header "Running Tests"

    try {
        python run_tests.py --all --verbose
        Write-Success "All tests completed"
        return $true
    }
    catch {
        Write-Error-Custom "Tests failed"
        return $false
    }
}

function Invoke-Clean {
    Write-Header "Cleaning Build Artifacts"

    $cleanDirs = @("dist", "build", "__pycache__", "*.spec")

    foreach ($dir in $cleanDirs) {
        if (Test-Path $dir) {
            Write-Info "Removing $dir..."
            Remove-Item $dir -Recurse -Force
        }
    }

    Write-Success "Cleanup completed"
    return $true
}

function Show-Help {
    Write-Header "Ultimate Focus Timer Build System"

    Write-Host "Available commands:" -ForegroundColor Cyan
    Write-Host "  setup     - Install all dependencies and run setup" -ForegroundColor White
    Write-Host "  build     - Build executable only" -ForegroundColor White
    Write-Host "  package   - Create distribution package" -ForegroundColor White
    Write-Host "  release   - Full release process with version bump" -ForegroundColor White
    Write-Host "  quick     - Quick build (deps + executable)" -ForegroundColor White
    Write-Host "  test      - Run test suite" -ForegroundColor White
    Write-Host "  clean     - Clean build artifacts" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Force    - Force reinstall dependencies" -ForegroundColor White
    Write-Host "  -Verbose  - Enable verbose output" -ForegroundColor White
    Write-Host "  -NoTest   - Skip tests in release process" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\build.ps1 quick" -ForegroundColor White
    Write-Host "  .\build.ps1 release -NoTest" -ForegroundColor White
    Write-Host "  .\build.ps1 setup -Force" -ForegroundColor White
}

# Main execution
try {
    switch ($Command.ToLower()) {
        "setup" {
            $success = Invoke-Setup
        }
        "build" {
            $success = Invoke-Build
        }
        "package" {
            $success = Invoke-Package
        }
        "release" {
            $success = Invoke-Release
        }
        "quick" {
            $success = Invoke-QuickBuild
        }
        "test" {
            $success = Invoke-Test
        }
        "clean" {
            $success = Invoke-Clean
        }
        default {
            Show-Help
            exit 0
        }
    }

    if ($success) {
        Write-Host ""
        Write-Success "Operation completed successfully! 🎉"
    }
    else {
        Write-Host ""
        Write-Error-Custom "Operation failed! ❌"
        exit 1
    }
}
catch {
    Write-Host ""
    Write-Error-Custom "Unexpected error: $_"
    exit 1
}

Write-Host ""
