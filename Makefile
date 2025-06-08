# Ultimate Focus Timer - Development Makefile
# Cross-platform development automation

.PHONY: help install install-dev test lint format type-check security clean build docs serve run

# Default target
help:
	@echo "Ultimate Focus Timer - Development Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Quality Commands:"
	@echo "  test         Run test suite"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  type-check   Run type checking with mypy"
	@echo "  security     Run security scans"
	@echo "  quality      Run all quality checks"
	@echo ""
	@echo "Development Commands:"
	@echo "  run          Run the application"
	@echo "  run-gui      Run GUI version"
	@echo "  run-console  Run console version"
	@echo "  serve        Start development dashboard"
	@echo ""
	@echo "Build Commands:"
	@echo "  build        Build distribution packages"
	@echo "  docs         Generate documentation"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "Git Commands:"
	@echo "  hooks        Install pre-commit hooks"
	@echo "  status       Show git status"

# Installation
install:python-m pip install --upgrade pip

python-m pip install -r requirements.txt

install-dev: install

python-m pip install -r requirements-dev.txt

python-m pip install -e .

# Testing
test:

python-m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-quick:

python-m pytest tests/ -x -v

# Code quality
lint:

python-m flake8 src/ tests/ main.py focus_app.py

python-m pydocstyle src/

format:

python-m black src/ tests/ main.py focus_app.py setup.py

python-m isort src/ tests/ main.py focus_app.py setup.py

type-check:

python-m mypy src/ main.py focus_app.py

security:

python-m safety check

python-m bandit -r src/ -f json -o bandit-report.json || true

python-m bandit -r src/

quality: lint type-check security test

# Development
run:

pythonmain.py

run-gui:

pythonfocus_app.py --gui

run-console:

pythonfocus_app.py --console

serve:

python-c "from src.dashboard import Dashboard; Dashboard().run_server(debug=True)"

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "API documentation would be generated here"

# Build and distribution
build: clean

python-m build

clean:
	@echo "Cleaning build artifacts..."
	@if exist build rmdir /s /q build 2>nul || true
	@if exist dist rmdir /s /q dist 2>nul || true
	@if exist *.egg-info rmdir /s /q *.egg-info 2>nul || true
	@if exist __pycache__ rmdir /s /q __pycache__ 2>nul || true
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul || true
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d" 2>nul || true
	@if exist .coverage del .coverage 2>nul || true
	@if exist htmlcov rmdir /s /q htmlcov 2>nul || true
	@if exist .pytest_cache rmdir /s /q .pytest_cache 2>nul || true
	@if exist .mypy_cache rmdir /s /q .mypy_cache 2>nul || true

# Git hooks
hooks:

python-m pre_commit install

python-m pre_commit install --hook-type commit-msg

# Git status
status:
gitstatus--porcelain --branch

# Environment setup
venv:

python-m venv .venv
	@echo "Virtual environment created. Activate with:"
	@echo "Windows: .venv\Scripts\activate"
	@echo "Unix/Mac: source .venv/bin/activate"

# Quick development setup
setup: venv install-dev hooks
	@echo "Development environment setup complete!"
	@echo "Activate virtual environment and run 'make run' to start."
