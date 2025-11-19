#!/usr/bin/env python3
"""
Simple build script for Focus Timer using PyInstaller
"""

import subprocess
import sys


def build():
    """Build the application using PyInstaller with simple command line args"""

    print("Building Focus Timer executable...")

    # Simple PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=focus",
        "--onefile",
        "--noconsole",  # No console window for GUI app
        "--icon=files/icon.png",
        "--add-data=files;files",
        "--add-data=src;src",
        "--add-data=config.yml;.",
        "--add-data=data;data",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=yaml",
        "--hidden-import=psutil",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=pandas",
        "--hidden-import=PIL",
        "--hidden-import=plyer.platforms.win.notification",
        "--hidden-import=rich",
        "--hidden-import=colorama",
        "--hidden-import=seaborn",
        "main.py",
    ]

    print("Running command:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed successfully!")
        print("Executable created in: dist/focus.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\nBuild failed with error: {e}")
        return False


if __name__ == "__main__":
    build()
