#!/usr/bin/env python3
"""
Debug version of the GUI to help identify startup issues
"""

import sys
import traceback
from pathlib import Path

# Add current directory and src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Startup info - minimal
print(f"Exec: {sys.executable}, Ver: {sys.version.split()[0]}")

try:
    # Launch GUI
    from src.focus_gui import FocusGUI

    app = FocusGUI()
    app.run()

    # GUI session ended
    print("GUI closed")

except ImportError as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)
