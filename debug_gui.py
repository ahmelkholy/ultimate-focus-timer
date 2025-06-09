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

print("=== GUI Debug Startup ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Working directory: {Path.cwd()}")
print(f"Script location: {Path(__file__).parent}")
print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths

try:
    print("Importing dependencies...")
    from src.focus_gui import FocusGUI
    print("✅ Dependencies imported successfully")

    print("Creating GUI instance...")
    app = FocusGUI()
    print("✅ GUI instance created successfully")

    print("Starting GUI mainloop...")
    app.run()
    print("✅ GUI completed normally")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📝 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Runtime error: {e}")
    print("📝 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
