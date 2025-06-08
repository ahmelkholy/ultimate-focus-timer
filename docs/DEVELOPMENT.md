# Ultimate Focus Timer - Development Guide

This guide covers the development setup, workflow, and best practices for contributing to the Ultimate Focus Timer project.

## Quick Start

### Windows (PowerShell)
```powershell
# Clone and setup
git clone <repository-url>
cd ultimate-focus-timer
.\dev.ps1 setup
```

### Unix/Linux/macOS
```bash
# Clone and setup
git clone <repository-url>
cd ultimate-focus-timer
make setup
```

## Development Environment

### Prerequisites
- Python 3.8+ (3.12 recommended)
- Git
- Virtual environment support

### Setup Commands

| Platform | Command | Description |
|----------|---------|-------------|
| Windows | `.\dev.ps1 setup` | Complete development setup |
| Unix/Mac | `make setup` | Complete development setup |

This will:
1. Create a virtual environment
2. Install all dependencies
3. Set up pre-commit hooks
4. Prepare the development environment

## Project Structure

```
ultimate-focus-timer/
├── src/                    # Source code modules
│   ├── __init__.py        # Package initialization
│   ├── __version__.py     # Version information
│   ├── config_manager.py  # Configuration management
│   ├── session_manager.py # Session handling
│   ├── music_controller.py # Audio control
│   ├── notification_manager.py # Notifications
│   ├── focus_gui.py       # GUI interface
│   ├── focus_console.py   # Console interface
│   ├── dashboard.py       # Web dashboard
│   └── cli.py            # Command-line interface
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_core.py      # Core functionality tests
│   └── test_utils.py     # Utility tests
├── docs/                  # Documentation
│   ├── USER_GUIDE.md     # User documentation
│   ├── CHANGELOG.md      # Version history
│   ├── CONTRIBUTING.md   # Contribution guidelines
│   └── VENV_SETUP.md     # Virtual environment guide
├── .github/               # GitHub workflows
│   └── workflows/
│       └── ci.yml        # CI/CD pipeline
├── main.py               # Main entry point
├── focus_app.py          # GUI application launcher
├── setup.py              # Legacy setup script
├── pyproject.toml        # Modern Python packaging
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── Makefile              # Unix development commands
├── dev.ps1              # Windows development script
└── README.md            # Project overview
```

## Development Workflow

### 1. Environment Activation

**Windows:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Unix/Mac:**
```bash
source .venv/bin/activate
```

### 2. Development Commands

| Task | Windows | Unix/Mac | Description |
|------|---------|----------|-------------|
| Run application | `.\dev.ps1 run` | `make run` | Start the focus timer |
| Run GUI | `.\dev.ps1 run-gui` | `make run-gui` | Launch GUI interface |
| Run console | `.\dev.ps1 run-console` | `make run-console` | Launch console interface |
| Run tests | `.\dev.ps1 test` | `make test` | Execute test suite |
| Run tests with coverage | `.\dev.ps1 test-cov` | `make test` | Tests + coverage report |
| Format code | `.\dev.ps1 format` | `make format` | Auto-format code |
| Lint code | `.\dev.ps1 lint` | `make lint` | Run linting checks |
| Type check | | `make type-check` | Run mypy type checking |
| Security scan | `.\dev.ps1 security` | `make security` | Security vulnerability scan |
| Quality check | `.\dev.ps1 quality` | `make quality` | All quality checks |
| Build package | `.\dev.ps1 build` | `make build` | Build distribution |
| Clean artifacts | `.\dev.ps1 clean` | `make clean` | Remove build files |

### 3. Code Quality Standards

#### Formatting
- **Black** for code formatting (line length: 88)
- **isort** for import sorting
- Configuration in `pyproject.toml`

#### Linting
- **flake8** for style checking
- **mypy** for type checking
- **pydocstyle** for docstring conventions

#### Security
- **bandit** for security issue detection
- **safety** for dependency vulnerability checking

#### Testing
- **pytest** for test framework
- **pytest-cov** for coverage reporting
- Target: >90% code coverage

### 4. Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
# Install hooks (done automatically in setup)
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

Hooks include:
- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit)
- Documentation checks

### 5. Testing Strategy

#### Test Structure
```
tests/
├── test_core.py      # Core functionality
├── test_utils.py     # Utilities and fixtures
├── test_gui.py       # GUI components (future)
├── test_cli.py       # CLI components (future)
└── conftest.py       # Shared fixtures (future)
```

#### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_core.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

#### Writing Tests
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Include both positive and negative test cases
- Test edge cases and error conditions

### 6. Documentation

#### Code Documentation
- Use Google-style docstrings
- Document all public functions and classes
- Include type hints where possible
- Add inline comments for complex logic

#### User Documentation
- Keep `README.md` updated with major changes
- Update `docs/USER_GUIDE.md` for user-facing features
- Document configuration options
- Include examples and screenshots

### 7. Version Management

Version information is centralized in `src/__version__.py`:

```python
__version__ = "1.0.0"
VERSION_INFO = (1, 0, 0)
```

### 8. Dependency Management

#### Adding Dependencies
1. Add to `requirements.txt` for production dependencies
2. Add to `requirements-dev.txt` for development tools
3. Update `pyproject.toml` dependencies list
4. Test installation in clean environment

#### Updating Dependencies
```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements files
pip freeze > requirements.txt
```

### 9. Git Workflow

#### Branch Strategy
- `main` - stable release branch
- `develop` - development integration branch
- `feature/*` - feature development branches
- `bugfix/*` - bug fix branches
- `hotfix/*` - urgent production fixes

#### Commit Messages
Follow conventional commit format:
```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- style: formatting changes
- refactor: code restructuring
- test: adding tests
- chore: maintenance tasks
```

#### Pull Request Process
1. Create feature branch from `develop`
2. Make changes with tests
3. Ensure all quality checks pass
4. Update documentation if needed
5. Submit pull request with clear description
6. Address review feedback
7. Merge after approval

### 10. Release Process

#### Preparation
1. Update version in `src/__version__.py`
2. Update `docs/CHANGELOG.md`
3. Run full quality check: `make quality`
4. Test installation in clean environment
5. Update documentation

#### Release Steps
1. Merge to `main` branch
2. Create git tag: `git tag v1.0.0`
3. Build distribution: `make build`
4. Upload to PyPI (if applicable)
5. Create GitHub release with changelog
6. Update `develop` branch

### 11. Troubleshooting

#### Common Issues

**Import Errors**
```bash
# Ensure virtual environment is activated
# Check Python path includes src/
python -c "import sys; print(sys.path)"
```

**Test Failures**
```bash
# Run specific failing test
pytest tests/test_core.py::TestConfigManager::test_config_creation -v

# Check test dependencies
pip install -r requirements-dev.txt
```

**Pre-commit Hook Failures**
```bash
# Run hooks manually to see detailed errors
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

**Virtual Environment Issues**
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 12. Development Tools

#### Recommended IDE Setup
- **VS Code** with Python extension
- **PyCharm** Professional or Community
- Extensions: Python, GitLens, Better Comments

#### Useful Commands
```bash
# Check code complexity
flake8 --max-complexity=10 src/

# Profile performance
python -m cProfile -o profile.stats main.py

# Generate documentation
sphinx-build -b html docs/ docs/_build/

# Security scan
bandit -r src/ -f json -o security-report.json
```

### 13. Contributing Guidelines

Please read `docs/CONTRIBUTING.md` for detailed contribution guidelines, including:
- Code of conduct
- Issue reporting
- Feature requests
- Development setup
- Pull request process

### 14. Support and Community

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check `docs/` directory for detailed guides
- **Examples**: See `examples/` directory for usage examples

---

For more information, see:
- [User Guide](docs/USER_GUIDE.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)
- [Virtual Environment Setup](docs/VENV_SETUP.md)
