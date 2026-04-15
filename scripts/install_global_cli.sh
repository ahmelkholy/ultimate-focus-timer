#!/bin/bash
# Global CLI alias installer for Ultimate Focus Timer - Portable Version

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🎯 Ultimate Focus Timer - Global CLI Installer"
echo "=============================================="

# Find the best Python executable (local venv is priority)
if [ -f "$PROJECT_ROOT/.venv/bin/python3" ]; then
    PYTHON_EXE="$PROJECT_ROOT/.venv/bin/python3"
elif [ -f "$PROJECT_ROOT/venv/bin/python3" ]; then
    PYTHON_EXE="$PROJECT_ROOT/venv/bin/python3"
else
    # Fallback to system python3 if venv not found
    PYTHON_EXE="python3"
fi

FOCUS_SCRIPT="$SCRIPT_DIR/focus"
chmod +x "$FOCUS_SCRIPT"

# Detect shell
SHELL_NAME=$(basename "$SHELL")
RC_FILE=""

case "$SHELL_NAME" in
    bash)
        RC_FILE="$HOME/.bashrc"
        # On macOS, bash uses .bash_profile usually
        if [[ "$OSTYPE" == "darwin"* ]] && [ ! -f "$RC_FILE" ]; then
            RC_FILE="$HOME/.bash_profile"
        fi
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    *)
        echo "⚠️  Unknown shell: $SHELL_NAME. Defaulting to .profile"
        RC_FILE="$HOME/.profile"
        ;;
esac

# Create the exact alias command
ALIAS_CMD="alias focus='$PYTHON_EXE $FOCUS_SCRIPT'"

# Check if alias already exists and update or add it
if [ -f "$RC_FILE" ] && grep -q "alias focus=" "$RC_FILE"; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed requires an empty string for the -i flag
        sed -i '' "s|alias focus=.*|$ALIAS_CMD|" "$RC_FILE"
    else
        sed -i "s|alias focus=.*|$ALIAS_CMD|" "$RC_FILE"
    fi
    echo "✅ Updated existing 'focus' alias in $RC_FILE"
else
    echo "" >> "$RC_FILE"
    echo "# Ultimate Focus Timer" >> "$RC_FILE"
    echo "$ALIAS_CMD" >> "$RC_FILE"
    echo "✅ Added 'focus' alias to $RC_FILE"
fi

echo ""
echo "📋 Setup complete! Reload your shell to apply changes:"
echo "   source $RC_FILE"
echo ""
echo "Usage:"
echo "   focus gui     - Launch the interface"
echo "   focus start   - Start Ultradian session"
echo "   focus status  - Show session status"
echo "   focus stop    - End current session"
