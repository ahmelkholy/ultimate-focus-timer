#!/bin/bash
# Global CLI alias installer for Ultimate Focus Timer

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FOCUS_SCRIPT="$SCRIPT_DIR/focus"

echo "🎯 Ultimate Focus Timer - Global CLI Installer"
echo "=" "=============================================="
echo ""

# Make script executable
chmod +x "$FOCUS_SCRIPT"

# Detect shell
SHELL_NAME=$(basename "$SHELL")
RC_FILE=""

case "$SHELL_NAME" in
    bash)
        RC_FILE="$HOME/.bashrc"
        ;;
    zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    fish)
        RC_FILE="$HOME/.config/fish/config.fish"
        echo "❌ Fish shell not yet supported. Please add manually:"
        echo "   alias focus='python $FOCUS_SCRIPT'"
        exit 1
        ;;
    *)
        echo "❌ Unknown shell: $SHELL_NAME"
        echo "Please add this alias manually to your shell RC file:"
        echo "   alias focus='python $FOCUS_SCRIPT'"
        exit 1
        ;;
esac

# Check if alias already exists
if grep -q "alias focus=" "$RC_FILE" 2>/dev/null; then
    echo "✅ 'focus' alias already exists in $RC_FILE"
else
    echo "" >> "$RC_FILE"
    echo "# Ultimate Focus Timer global CLI" >> "$RC_FILE"
    echo "alias focus='python $FOCUS_SCRIPT'" >> "$RC_FILE"
    echo "✅ Added 'focus' alias to $RC_FILE"
fi

echo ""
echo "📋 Setup complete! Reload your shell:"
echo "   source $RC_FILE"
echo ""
echo "Then use:"
echo "   focus start   - Start Ultradian session"
echo "   focus stop    - Stop current session"
echo "   focus status  - Show session status"
echo "   focus daemon  - Start background daemon"
