# Ultimate Focus Timer - PowerShell Development Script
# Windows-specific automation for development tasks

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [switch]$Verbose,
    [switch]$Force
)

# Set strict mode and error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir
$SrcDir = Join-Path $ProjectRoot "src"
$TestsDir = Join-Path $ProjectRoot "tests"
$VenvDir = Join-Path $ProjectRoot ".venv"

# Color output functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }

# Check if virtual environment exists
function Test-VirtualEnvironment {
    return Test-Path $VenvDir
}

# Activate virtual environment
function Enable-VirtualEnvironment {
    if (Test-VirtualEnvironment) {
        $ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
        if (Test-Path $ActivateScript) {
            & $ActivateScript
            Write-Success "Virtual environment activated"
        } else {
            Write-Error "Virtual environment activation script not found"
            exit 1
        }
    } else {
        Write-Error "Virtual environment not found. Run 'setup' first."
        exit 1
    }
}

# Create virtual environment
function New-VirtualEnvironment {
    Write-Info "Creating virtual environment..."
    python -m venv $VenvDir
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created successfully"
    } else {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Install dependencies
function Install-Dependencies {
    param([switch]$Dev)

    Write-Info "Installing dependencies..."
    python -m pip install --upgrade pip

    if (Test-Path "requirements.txt") {
        python -m pip install -r requirements.txt
    }

    if ($Dev -and (Test-Path "requirements-dev.txt")) {
        python -m pip install -r requirements-dev.txt
    }

    # Install package in editable mode
    python -m pip install -e .

    Write-Success "Dependencies installed successfully"
}

# Run tests
function Invoke-Tests {
    param([switch]$Coverage, [switch]$Verbose)

    Write-Info "Running tests..."

    $TestArgs = @("tests/")
    if ($Coverage) { $TestArgs += @("--cov=src", "--cov-report=html", "--cov-report=term") }
    if ($Verbose) { $TestArgs += "-v" }

    python -m pytest @TestArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Success "All tests passed!"
    } else {
        Write-Error "Some tests failed"
        exit 1
    }
}

# Format code
function Format-Code {
    Write-Info "Formatting code..."

    $FilesToFormat = @("src/", "tests/", "main.py", "focus_app.py", "setup.py")

    # Run black formatter
    python -m black @FilesToFormat

    # Run isort
    python -m isort @FilesToFormat

    Write-Success "Code formatted successfully"
}

# Run linting
function Invoke-Linting {
    Write-Info "Running linting checks..."

    # Flake8
    python -m flake8 src/ tests/ main.py focus_app.py

    # Type checking
    python -m mypy src/ main.py focus_app.py

    Write-Success "Linting completed"
}

# Security checks
function Invoke-SecurityCheck {
    Write-Info "Running security checks..."

    # Safety check
    python -m safety check

    # Bandit security scan
    python -m bandit -r src/

    Write-Success "Security checks completed"
}

# Clean build artifacts
function Clear-BuildArtifacts {
    Write-Info "Cleaning build artifacts..."

    $DirsToRemove = @("build", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", "htmlcov")
    $FilesToRemove = @("*.egg-info", ".coverage")

    foreach ($dir in $DirsToRemove) {
        Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Name $dir -ErrorAction SilentlyContinue |
            ForEach-Object { Remove-Item -Path $_ -Recurse -Force }
    }

    foreach ($pattern in $FilesToRemove) {
        Get-ChildItem -Path $ProjectRoot -Recurse -File -Name $pattern -ErrorAction SilentlyContinue |
            ForEach-Object { Remove-Item -Path $_ -Force }
    }

    Write-Success "Build artifacts cleaned"
}

# Build distribution
function Build-Distribution {
    Write-Info "Building distribution packages..."

    Clear-BuildArtifacts
    python -m build

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Distribution built successfully"
        Write-Info "Distribution files:"
        Get-ChildItem -Path (Join-Path $ProjectRoot "dist") | ForEach-Object { Write-Host "  $($_.Name)" }
    } else {
        Write-Error "Build failed"
        exit 1
    }
}

# Run application
function Start-Application {
    param([string]$Mode = "default")

    switch ($Mode) {
        "gui" { python focus_app.py --gui }
        "console" { python focus_app.py --console }
        "dashboard" { python -c "from src.dashboard import Dashboard; Dashboard().run_server(debug=True)" }
        default { python main.py }
    }
}

# Install pre-commit hooks
function Install-PreCommitHooks {
    Write-Info "Installing pre-commit hooks..."
    python -m pre_commit install
    python -m pre_commit install --hook-type commit-msg
    Write-Success "Pre-commit hooks installed"
}

# Show project status
function Show-Status {
    Write-Info "Project Status"
    Write-Host "=============="

    # Virtual environment
    if (Test-VirtualEnvironment) {
        Write-Success "✓ Virtual environment exists"
    } else {
        Write-Warning "✗ Virtual environment missing"
    }

    # Dependencies
    if (Test-Path "requirements.txt") {
        Write-Success "✓ Requirements file exists"
    }

    # Source files
    $SourceFiles = Get-ChildItem -Path $SrcDir -Filter "*.py" -ErrorAction SilentlyContinue
    Write-Info "Source files: $($SourceFiles.Count)"

    # Test files
    $TestFiles = Get-ChildItem -Path $TestsDir -Filter "*.py" -ErrorAction SilentlyContinue
    Write-Info "Test files: $($TestFiles.Count)"

    # Git status
    if (Get-Command git -ErrorAction SilentlyContinue) {
        Write-Info "`nGit status:"
        git status --porcelain --branch
    }
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" {
        Write-Host "Ultimate Focus Timer - Development Commands" -ForegroundColor Magenta
        Write-Host "==========================================="
        Write-Host ""
        Write-Host "Setup Commands:"
        Write-Host "  setup        Complete development environment setup"
        Write-Host "  venv         Create virtual environment"
        Write-Host "  install      Install production dependencies"
        Write-Host "  install-dev  Install development dependencies"
        Write-Host ""
        Write-Host "Quality Commands:"
        Write-Host "  test         Run test suite"
        Write-Host "  test-cov     Run tests with coverage"
        Write-Host "  lint         Run linting checks"
        Write-Host "  format       Format code"
        Write-Host "  security     Run security checks"
        Write-Host "  quality      Run all quality checks"
        Write-Host ""
        Write-Host "Development Commands:"
        Write-Host "  run          Run the application"
        Write-Host "  run-gui      Run GUI version"
        Write-Host "  run-console  Run console version"
        Write-Host "  dashboard    Start development dashboard"
        Write-Host ""
        Write-Host "Build Commands:"
        Write-Host "  build        Build distribution"
        Write-Host "  clean        Clean build artifacts"
        Write-Host ""
        Write-Host "Utility Commands:"
        Write-Host "  status       Show project status"
        Write-Host "  hooks        Install pre-commit hooks"
    }

    "setup" {
        New-VirtualEnvironment
        Enable-VirtualEnvironment
        Install-Dependencies -Dev
        Install-PreCommitHooks
        Write-Success "Development environment setup complete!"
    }

    "venv" { New-VirtualEnvironment }
    "install" { Enable-VirtualEnvironment; Install-Dependencies }
    "install-dev" { Enable-VirtualEnvironment; Install-Dependencies -Dev }

    "test" { Enable-VirtualEnvironment; Invoke-Tests }
    "test-cov" { Enable-VirtualEnvironment; Invoke-Tests -Coverage }
    "lint" { Enable-VirtualEnvironment; Invoke-Linting }
    "format" { Enable-VirtualEnvironment; Format-Code }
    "security" { Enable-VirtualEnvironment; Invoke-SecurityCheck }
    "quality" {
        Enable-VirtualEnvironment
        Format-Code
        Invoke-Linting
        Invoke-SecurityCheck
        Invoke-Tests -Coverage
    }

    "run" { Enable-VirtualEnvironment; Start-Application }
    "run-gui" { Enable-VirtualEnvironment; Start-Application -Mode "gui" }
    "run-console" { Enable-VirtualEnvironment; Start-Application -Mode "console" }
    "dashboard" { Enable-VirtualEnvironment; Start-Application -Mode "dashboard" }

    "build" { Enable-VirtualEnvironment; Build-Distribution }
    "clean" { Clear-BuildArtifacts }

    "status" { Show-Status }
    "hooks" { Enable-VirtualEnvironment; Install-PreCommitHooks }

    default {
        Write-Error "Unknown command: $Command"
        Write-Info "Run './dev.ps1 help' for available commands"
        exit 1
    }
}
