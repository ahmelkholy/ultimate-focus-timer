#!/usr/bin/env python3
"""
Test script to verify that the Focus Timer executable works correctly
"""

import subprocess
import sys
from pathlib import Path


def test_executable():
    """Test the built executable"""
    exe_path = Path("dist") / "focus.exe"

    if not exe_path.exists():
        print("❌ ERROR: focus.exe not found in dist folder")
        return False

    print(f"✅ Found executable: {exe_path}")

    # Test version command
    try:
        result = subprocess.run(
            [str(exe_path), "--version"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("✅ Version command works")
            print(f"   Output: {result.stdout.strip()}")
        else:
            print("❌ Version command failed")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Version command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running version command: {e}")
        return False

    # Test help command
    try:
        result = subprocess.run(
            [str(exe_path), "--help"], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print("✅ Help command works")
        else:
            print("❌ Help command failed")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running help command: {e}")
        return False

    # Test check command (if available)
    try:
        result = subprocess.run(
            [str(exe_path), "check"], capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print("✅ Check command works")
        else:
            print("⚠️  Check command returned non-zero exit code (this might be normal)")
            if "Error importing modules" in result.stdout:
                print("❌ Module import errors detected!")
                print(f"   Output: {result.stdout}")
                return False
    except subprocess.TimeoutExpired:
        print("❌ Check command timed out")
        return False
    except Exception as e:
        print(f"⚠️  Error running check command: {e}")

    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    print("Testing Focus Timer executable...")
    print("=" * 50)

    success = test_executable()

    print("=" * 50)
    if success:
        print("🎉 All tests passed! The executable should work correctly.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Please check the build configuration.")
        sys.exit(1)
        sys.exit(1)
