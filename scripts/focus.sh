#!/bin/bash
# Focus Timer Launcher Script for Git Bash / WSL
# This script activates the virtual environment and launches Focus Timer

# Focus Timer installation path
FOCUS_PATH="/c/Users/ahm_e/AppData/Local/focus"
VENV_ACTIVATE="$FOCUS_PATH/.venv/Scripts/activate"
MAIN_SCRIPT="$FOCUS_PATH/main.py"

# Check if installation exists
if [ ! -d "$FOCUS_PATH" ]; then
    echo "❌ Focus Timer not found at: $FOCUS_PATH"
    echo "💡 Please ensure the Focus Timer is properly installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "❌ Virtual environment not found at: $VENV_ACTIVATE"
    echo "💡 Please run setup to create the virtual environment."
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Main launcher not found at: $MAIN_SCRIPT"
    echo "💡 Please verify the Focus Timer installation."
    exit 1
fi

# Save current directory
ORIGINAL_DIR=$(pwd)

# Change to Focus Timer directory
cd "$FOCUS_PATH" || exit 1

# Activate virtual environment
source "$VENV_ACTIVATE"

# Parse command line arguments
case "$1" in
    "")
        # No parameters - show interactive launcher
        python "$MAIN_SCRIPT"
        ;;
    "gui")
        python "$MAIN_SCRIPT" --gui
        ;;
    "console")
        python "$MAIN_SCRIPT" --console
        ;;
    "dashboard")
        python "$MAIN_SCRIPT" --dashboard
        ;;
    "stats")
        python "$MAIN_SCRIPT" --stats
        ;;
    "quick")
        if [ -n "$2" ]; then
            python "$MAIN_SCRIPT" --quick-session "$2"
        else
            python "$MAIN_SCRIPT" --quick-session 25  # Default 25 minutes
        fi
        ;;
    "break")
        if [ -n "$2" ]; then
            python "$MAIN_SCRIPT" --quick-break "$2"
        else
            python "$MAIN_SCRIPT" --quick-break 5   # Default 5 minutes
        fi
        ;;
    "check")
        python "$MAIN_SCRIPT" --check-deps
        ;;
    "info")
        python "$MAIN_SCRIPT" --sys-info
        ;;
    "interactive")
        python "$MAIN_SCRIPT" --interactive
        ;;
    --*)
        python "$MAIN_SCRIPT" "$@"
        ;;
    *)
        echo "❌ Unknown mode: $1"
        echo "📖 Available modes: gui, console, dashboard, quick [minutes], break [minutes], stats, check, info, interactive"
        echo "📝 Examples:"
        echo "   focus"
        echo "   focus gui"
        echo "   focus quick 25"
        echo "   focus break 5"
        echo "   focus stats"
        echo ""
        echo "👉 Forwarding arguments directly to main.py"
        python "$MAIN_SCRIPT" "$@"
        ;;
esac

# Restore original directory
cd "$ORIGINAL_DIR" || exit 1
