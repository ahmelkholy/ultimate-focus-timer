# Contributing to Ultimate Focus Timer

We welcome contributions to make Ultimate Focus Timer even better! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (Python 3.10+ recommended)
- Git for version control
- Basic understanding of the Pomodoro Technique
- Familiarity with Python development

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ultimate-focus-timer.git
   cd ultimate-focus-timer
   ```

3. **Set up virtual environment**:
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

5. **Run the application** to ensure everything works:
   ```bash
   python main.py --check-deps
   python main.py
   ```

## 🛠️ Development Guidelines

### Code Style

- **Follow PEP 8** - Use tools like `flake8` or `black` for code formatting
- **Type hints** - Include type hints for function parameters and return values
- **Docstrings** - Document all public methods and classes using Google-style docstrings
- **Comments** - Write clear, concise comments for complex logic

### Example Code Style

```python
def start_session(self, duration: int, session_type: str) -> bool:
    """Start a new focus session.

    Args:
        duration: Session duration in minutes
        session_type: Type of session ('work', 'short_break', 'long_break')

    Returns:
        bool: True if session started successfully, False otherwise

    Raises:
        ValueError: If duration is not positive or session_type is invalid
    """
    if duration <= 0:
        raise ValueError("Duration must be positive")

    # Implementation here
    return True
```

### Cross-Platform Compatibility

- **Test on multiple platforms** when possible (Windows, macOS, Linux)
- **Use `pathlib.Path`** instead of string paths
- **Handle platform-specific features** gracefully with fallbacks
- **Avoid hardcoded paths** - use configuration or platform detection

```python
import platform
from pathlib import Path

def get_config_dir() -> Path:
    """Get platform-appropriate configuration directory."""
    system = platform.system()
    if system == "Windows":
        return Path.home() / "AppData" / "Local" / "focus"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "focus"
    else:  # Linux
        return Path.home() / ".config" / "focus"
```

### Testing

- **Test your changes** before submitting
- **Include test cases** for new functionality
- **Verify cross-platform compatibility** when possible
- **Test with different Python versions** if available

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for custom notification sounds
fix: Resolve MPV path detection on macOS
docs: Update installation instructions
refactor: Simplify music controller initialization
test: Add unit tests for session manager
```

## 🐛 Reporting Issues

### Before Reporting

1. **Check existing issues** to avoid duplicates
2. **Update to the latest version** and test again
3. **Try basic troubleshooting**:
   ```bash
   python main.py --check-deps
   python main.py --info
   ```

### Issue Template

When reporting bugs, please include:

- **Environment information**:
  - Operating System and version
  - Python version
  - Application version

- **Steps to reproduce** the issue

- **Expected vs actual behavior**

- **Error messages** or logs (if any)

- **Screenshots** (if relevant)

## 💡 Feature Requests

We welcome feature suggestions! When requesting features:

1. **Check existing issues** and discussions
2. **Describe the use case** - why is this feature needed?
3. **Provide detailed specifications** - how should it work?
4. **Consider implementation complexity** - is it feasible?

### Feature Categories

We're particularly interested in:

- **New interface modes** (web interface, mobile companion, etc.)
- **Additional music sources** (Spotify integration, local music, etc.)
- **Enhanced analytics** (machine learning insights, productivity patterns)
- **Integrations** (task managers, calendar apps, etc.)
- **Accessibility improvements**
- **Performance optimizations**

## 🔧 Types of Contributions

### Code Contributions

- **Bug fixes** - Fix existing issues
- **New features** - Implement requested functionality
- **Performance improvements** - Optimize existing code
- **Cross-platform support** - Improve compatibility
- **Code refactoring** - Improve code structure and maintainability

### Documentation

- **README improvements** - Clarify instructions
- **Code documentation** - Add docstrings and comments
- **User guides** - Create tutorials and how-to guides
- **API documentation** - Document public interfaces

### Testing

- **Unit tests** - Test individual components
- **Integration tests** - Test component interactions
- **Platform testing** - Verify cross-platform compatibility
- **User acceptance testing** - Test real-world usage scenarios

### Design & UX

- **UI/UX improvements** - Enhance user interfaces
- **Theme contributions** - Create new color schemes
- **Icon design** - Improve visual elements
- **Accessibility** - Make the app more accessible

## 📋 Pull Request Process

### Before Submitting

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the guidelines above

3. **Test thoroughly**:
   ```bash
   python main.py --check-deps
   # Test different interfaces
   python main.py --gui
   python main.py --console
   python main.py --dashboard
   ```

4. **Update documentation** if needed

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

### Submitting the Pull Request

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub

3. **Fill out the PR template** with:
   - Description of changes
   - Testing performed
   - Screenshots (if UI changes)
   - Breaking changes (if any)

### Pull Request Review

- **Be responsive** to feedback and questions
- **Make requested changes** promptly
- **Keep PR focused** - one feature/fix per PR
- **Squash commits** if requested

## 🌟 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **README acknowledgments** section

## 🤝 Community Guidelines

### Be Respectful

- **Use inclusive language**
- **Be constructive** in feedback
- **Respect different perspectives**
- **Help newcomers** get started

### Communication

- **Use GitHub Issues** for bug reports and feature requests
- **Use GitHub Discussions** for questions and general discussion
- **Be clear and concise** in communication
- **Provide context** when asking questions

## 📚 Resources

### Learning Resources

- [Python Official Documentation](https://docs.python.org/)
- [Pomodoro Technique Guide](https://en.wikipedia.org/wiki/Pomodoro_Technique)
- [Cross-Platform Python Development](https://docs.python.org/3/library/platform.html)

### Development Tools

- **Code Editors**: VS Code, PyCharm, Sublime Text
- **Linting**: flake8, pylint, black
- **Testing**: pytest, unittest
- **Documentation**: Sphinx, MkDocs

## ❓ Questions

If you have questions about contributing:

1. Check the [GitHub Discussions](https://github.com/yourusername/ultimate-focus-timer/discussions)
2. Open a new discussion with the "Q&A" category
3. Tag your question appropriately

---

Thank you for contributing to Ultimate Focus Timer! Together, we can build an amazing productivity tool for everyone. 🎯
