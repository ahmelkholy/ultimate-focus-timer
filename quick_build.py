#!/usr/bin/env python3
"""
Quick Build and Package Script
Simplified script to quickly build executables
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, check=True, shell=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main build function"""
    print("🎯 Ultimate Focus Timer - Quick Build")
    print("====================================")

    # Install build dependencies
    if not run_command(
        f"{sys.executable} -m pip install -r requirements-build.txt",
        "Installing build dependencies"
    ):
        return False

    # Run full build
    if not run_command(
        f"{sys.executable} build_config.py all",
        "Building executable and creating installer"
    ):
        return False

    print("\n🎉 Build completed successfully!")
    print("📁 Check the 'dist' folder for your executable")
    print("📦 Archive files are ready for distribution")

    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
