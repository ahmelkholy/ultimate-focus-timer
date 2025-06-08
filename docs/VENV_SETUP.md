# 🎯 Virtual Environment Setup Guide

This guide helps you set up a proper Python virtual environment for the Ultimate Focus Timer project.

## 🐍 Why Use Virtual Environments?

Virtual environments provide:
- **Isolation**: Separate dependencies from your system Python
- **Reproducibility**: Consistent environment across different machines
- **Safety**: Prevent conflicts with other Python projects
- **Clean installs**: Easy to recreate if something goes wrong

## 🚀 Quick Setup

### 1. Create Virtual Environment

```pwsh
# Navigate to project directory
cd "c:\Users\ahm_e\AppData\Local\focus"

# Create virtual environment
python -m venv .venv
```

### 2. Activate Virtual Environment

```pwsh
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt
.\.venv\Scripts\activate.bat

# Git Bash on Windows
source .venv/Scripts/activate
```

### 3. Install Dependencies

```pwsh
# Upgrade pip first
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt
```

### 4. Verify Installation

```pwsh
# Check Python location (should be in .venv)
python -c "import sys; print(sys.executable)"

# Check installed packages
pip list

# Test application
python main.py --check-deps
```

## 🔧 Virtual Environment Management

### Activation Commands by Shell

| Shell | Command |
|-------|---------|
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Command Prompt | `.\.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |
| VS Code Terminal | Automatic (if configured) |

### Deactivation

```pwsh
# From any activated environment
deactivate
```

### Recreate Environment

```pwsh
# Remove existing environment
Remove-Item -Recurse -Force .venv

# Create new environment
python -m venv .venv

# Activate and install
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 🛠️ Development Workflow

### Daily Development

```pwsh
# 1. Navigate to project
cd "c:\Users\ahm_e\AppData\Local\focus"

# 2. Activate environment
.\.venv\Scripts\Activate.ps1

# 3. Work on code
# ... make your changes ...

# 4. Test changes
python main.py --gui
python main.py --console
python main.py --dashboard

# 5. Deactivate when done
deactivate
```

### Installing New Packages

```pwsh
# Activate environment first
.\.venv\Scripts\Activate.ps1

# Install package
pip install package-name

# Update requirements file
pip freeze > requirements.txt

# Or add manually to requirements.txt
```

### Running Different Interfaces

```pwsh
# Ensure environment is activated first
.\.venv\Scripts\Activate.ps1

# GUI Interface
python main.py --gui

# Console Interface
python main.py --console

# Analytics Dashboard
python main.py --dashboard

# Quick Pomodoro
python main.py --pomodoro
```

## 🎛️ VS Code Integration

### Automatic Environment Selection

1. **Open VS Code** in the project directory
2. **Press Ctrl+Shift+P** and type "Python: Select Interpreter"
3. **Choose** the `.venv\Scripts\python.exe` interpreter
4. **Terminal** will automatically activate the environment

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

## 🚨 Troubleshooting

### PowerShell Execution Policy

If you get execution policy errors:

```pwsh
# Check current policy
Get-ExecutionPolicy

# Set policy for current user (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Alternative: Bypass for single session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### Python Not Found

```pwsh
# Check Python installation
python --version

# If not found, install Python 3.8+
# Download from: https://python.org/downloads/

# Or use winget
winget install Python.Python.3.12
```

### Virtual Environment Not Working

```pwsh
# Remove and recreate
Remove-Item -Recurse -Force .venv
python -m venv .venv --clear

# Try different activation method
cmd /c ".venv\Scripts\activate.bat && python main.py"
```

### Package Installation Fails

```pwsh
# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install with no cache
pip install --no-cache-dir -r requirements.txt

# Install one by one to isolate issues
pip install PyYAML
pip install matplotlib
# ... etc
```

### Import Errors

```pwsh
# Check if packages are installed
pip list | findstr package-name

# Verify Python path
python -c "import sys; print('\n'.join(sys.path))"

# Check if environment is activated
python -c "import sys; print(sys.prefix)"
```

## 📦 Package Management

### Core Dependencies

```text
PyYAML>=6.0           # Configuration file handling
matplotlib>=3.5.0     # Charts and visualizations
pandas>=1.3.0         # Data analysis
seaborn>=0.11.0       # Statistical visualizations
plyer>=2.1.0          # Cross-platform notifications
psutil>=5.8.0         # System monitoring
rich>=13.0.0          # Rich terminal output
click>=8.0.0          # Command-line interface
```

### Development Dependencies

```text
black>=22.0.0         # Code formatting
flake8>=4.0.0         # Code linting
pytest>=7.0.0         # Testing framework
mypy>=0.950           # Type checking
```

### Optional Dependencies

```text
requests>=2.28.0      # HTTP requests (for online features)
pillow>=9.0.0         # Image processing
tkinter               # GUI framework (usually built-in)
```

## 🎯 Best Practices

### Environment Hygiene

- **Always activate** the environment before working
- **Keep requirements.txt updated** when adding packages
- **Use pinned versions** for production deployments
- **Document** any special installation requirements

### Development Tips

- **Use relative imports** for internal modules
- **Test in clean environment** before committing
- **Keep environment small** - only install what you need
- **Use virtual environments** for each project

### Git Integration

Add to `.gitignore`:

```gitignore
# Virtual Environment
.venv/
env/
venv/

# Python cache
__pycache__/
*.pyc
*.pyo
```

## 🔄 Migration from Global Installation

If you were using global Python packages:

```pwsh
# 1. Create requirements from global packages
pip freeze > global_requirements.txt

# 2. Create virtual environment
python -m venv .venv

# 3. Activate environment
.\.venv\Scripts\Activate.ps1

# 4. Install only needed packages
pip install -r requirements.txt

# 5. Test application
python main.py --check-deps
```

## 📞 Support

If you encounter issues with virtual environment setup:

1. **Check this guide** for common solutions
2. **Search existing issues** on GitHub
3. **Create new issue** with:
   - Your operating system
   - Python version
   - Error messages
   - Steps you tried

---

**Happy coding in your isolated environment! 🎯**
