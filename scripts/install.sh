#!/bin/bash
echo "Ultimate Focus Timer - Linux Installer"
echo "====================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

# Install system dependencies
if command -v apt &> /dev/null; then
    echo "Installing system dependencies (Ubuntu/Debian)..."
    sudo apt update
    sudo apt install -y python3-pip python3-tk mpv
elif command -v dnf &> /dev/null; then
    echo "Installing system dependencies (Fedora)..."
    sudo dnf install -y python3-pip python3-tkinter mpv
elif command -v pacman &> /dev/null; then
    echo "Installing system dependencies (Arch)..."
    sudo pacman -S python-pip tk mpv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Run setup
echo "Running setup..."
python3 setup.py

echo ""
echo "Installation completed!"
echo "Run './UltimateFocusTimer' to start the application"
