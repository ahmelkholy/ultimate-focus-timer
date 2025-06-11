# 📁 Focus Timer - Directory Organization

## 🎯 Clean Root Directory Structure

The root directory has been organized to reduce clutter and improve maintainability:

```
focus/
├── 📜 Core Files (Root)
│   ├── main.py                 # Main application entry point
│   ├── config.yml             # Configuration file
│   ├── requirements.txt       # Python dependencies
│   ├── README.md              # Project documentation
│   ├── CHANGELOG.md           # Version history
│   ├── CONTRIBUTING.md        # Contribution guidelines
│   └── LICENSE                # License file
│
├── 📂 Source Code
│   └── src/                   # All Python source code
│       ├── focus_gui.py       # GUI interface
│       ├── focus_app.py       # App launcher (moved from root)
│       ├── music_controller.py # Music functionality
│       └── ...                # Other modules
│
├── 🔧 Build & Development
│   └── build-tools/           # Build and development files
│       ├── pyproject.toml     # Project metadata
│       ├── setup.py           # Setup script
│       ├── Makefile           # Build automation
│       ├── focus_timer.spec   # PyInstaller spec
│       ├── install.bat        # Windows installer
│       └── requirements-*.txt # Development dependencies
│
├── 📚 Documentation
│   └── docs/                  # All documentation files
│       ├── PLAYLIST_SELECTION_COMPLETE.md
│       ├── ALIAS_SETUP_COMPLETE.md
│       ├── PROJECT_STATUS.md
│       ├── VENV_SETUP.md
│       └── development/       # Development docs
│
├── 🧪 Testing
│   └── tests/                 # Test files
│       └── temp/              # Temporary test files
│
├── 🗂️ Temporary Files
│   └── temp/                  # Temporary and demo files
│       ├── demo_playlist_selection.py
│       ├── test_playlist_*.py
│       └── *.pid              # Runtime files
│
├── 📊 Data & Output
│   ├── exports/               # CSV/JSON exports
│   ├── log/                   # Application logs
│   ├── music/                 # Music files
│   └── static/                # Static assets
│
├── 🏗️ Build Artifacts
│   ├── build/                 # Build output
│   ├── dist/                  # Distribution files
│   └── backups/               # Backup files
│
└── ⚙️ System Files
    ├── .git/                  # Git repository
    ├── .github/               # GitHub workflows
    ├── .vscode/               # VS Code settings
    ├── .venv/                 # Virtual environment
    └── scripts/               # Utility scripts
```

## 🎉 Benefits of This Organization

### ✅ Clean Root Directory

- Only essential files in root (main.py, config.yml, README.md, etc.)
- Easy to navigate and understand project structure
- Professional appearance

### ✅ Logical Grouping

- **build-tools/**: All build and development related files
- **docs/**: All documentation in one place
- **temp/**: Temporary files that can be safely deleted
- **src/**: All source code organized

### ✅ Easy Maintenance

- Clear separation of concerns
- Easy to find specific types of files
- Easier to add to .gitignore patterns

## 🚀 Usage After Organization

### Running the Application

```bash
# Still works the same way
python main.py --gui
python main.py --console
```

### Build and Development

```bash
# Build tools moved but still accessible
python build-tools/setup.py build
```

### Documentation

```bash
# All docs now in docs/ directory
cat docs/PLAYLIST_SELECTION_COMPLETE.md
```

### Temporary Files

```bash
# Temp files isolated in temp/ directory
# Can be safely deleted when not needed
rm -rf temp/
```

## 📝 Files Moved During Organization

### To `docs/`

- PLAYLIST_SELECTION_COMPLETE.md
- PLAYLIST_SELECTION_IMPLEMENTATION.md
- ALIAS_SETUP_COMPLETE.md
- PROJECT_STATUS.md
- VENV_SETUP.md

- # Code Citations.md

### To `build-tools/`

- pyproject.toml
- setup.py
- Makefile
- focus_timer.spec
- install.bat
- requirements-build.txt
- requirements-dev.txt

### To `src/`

- focus_app.py (moved from root)

### To `temp/`

- demo_playlist_selection.py
- test_playlist_selection.py
- test_playlist_feature.py

### Cleaned Up

- **pycache**/ (removed from root)
- mpv_classical.pid (moved to temp)
