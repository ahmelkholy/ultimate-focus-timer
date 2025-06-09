#!/usr/bin/env python3
"""
Release Management Script for Ultimate Focus Timer
Automates version bumping, building, and release preparation
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import argparse

class ReleaseManager:
    """Manages the release process for Ultimate Focus Timer"""

    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.version_file = self.root_dir / "src" / "__version__.py"
        self.changelog_file = self.root_dir / "CHANGELOG.md"

    def get_current_version(self):
        """Get current version from __version__.py"""
        try:
            with open(self.version_file, 'r') as f:
                content = f.read()
                match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)
        except FileNotFoundError:
            pass
        return "0.1.0"

    def bump_version(self, version_type="patch"):
        """Bump version number"""
        current = self.get_current_version()
        parts = current.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"

        # Update version file
        version_content = f'''"""
Ultimate Focus Timer Version Information
"""

__version__ = "{new_version}"
__author__ = "Ahmed Elkholy"
__email__ = "ahm_elkholy@outlook.com"
__description__ = "Ultimate cross-platform productivity timer"
__url__ = "https://github.com/ahmelkholy/ultimate-focus-timer"

# Build information
__build_date__ = "{datetime.now().isoformat()}"
__build_platform__ = "{sys.platform}"
'''

        os.makedirs(self.version_file.parent, exist_ok=True)
        with open(self.version_file, 'w') as f:
            f.write(version_content)

        print(f"✅ Version bumped from {current} to {new_version}")
        return new_version

    def update_changelog(self, version, changes=None):
        """Update changelog with new version"""
        date_str = datetime.now().strftime("%Y-%m-%d")

        if changes is None:
            changes = [
                "🎯 Performance improvements",
                "🐛 Bug fixes and stability enhancements",
                "📦 Updated dependencies",
                "🔧 Build system improvements"
            ]

        new_entry = f"""
## [{version}] - {date_str}

### Added
{chr(10).join(f"- {change}" for change in changes if "added" in change.lower() or "new" in change.lower())}

### Changed
{chr(10).join(f"- {change}" for change in changes if "changed" in change.lower() or "improved" in change.lower() or "performance" in change.lower())}

### Fixed
{chr(10).join(f"- {change}" for change in changes if "fix" in change.lower() or "bug" in change.lower())}

### Technical
{chr(10).join(f"- {change}" for change in changes if any(word in change.lower() for word in ["build", "package", "dependencies", "setup"]))}

"""

        # Read existing changelog
        try:
            with open(self.changelog_file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

        # Insert new entry after the header
        lines = content.split('\n')
        header_end = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#') and not line.startswith('All notable'):
                header_end = i
                break

        lines.insert(header_end, new_entry)

        with open(self.changelog_file, 'w') as f:
            f.write('\n'.join(lines))

        print(f"✅ Changelog updated for version {version}")

    def build_executable(self):
        """Build executable using build_config.py"""
        print("🔨 Building executable...")

        try:
            result = subprocess.run(
                [sys.executable, "build_config.py", "all"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                print("✅ Executable built successfully!")
                return True
            else:
                print(f"❌ Build failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Build timed out")
            return False
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False

    def create_github_release_notes(self, version):
        """Create release notes for GitHub"""
        notes = f"""# 🎯 Ultimate Focus Timer v{version}

## 🚀 What's New
- Enhanced cross-platform compatibility
- Improved performance and stability
- Better user experience
- Updated dependencies

## 📦 Downloads
Choose the appropriate version for your operating system:

### Windows
- **UltimateFocusTimer-windows.zip** - Complete Windows package with installer

### macOS
- **UltimateFocusTimer-macos.tar.gz** - macOS application bundle

### Linux
- **UltimateFocusTimer-linux.tar.gz** - Linux executable package

## 🛠️ Installation

### Quick Start
1. Download the appropriate package for your system
2. Extract the archive
3. Run the installer script or executable directly

### System Requirements
- Python 3.8+ (for source version)
- MPV Media Player (auto-installed by setup)
- 100MB available disk space

## 🎯 New Features
- 🎮 Multiple interface options (GUI, Console, Dashboard)
- 🎵 Classical music integration
- 📊 Advanced analytics and tracking
- 🔔 Smart notifications
- ⚙️ Highly configurable settings

## 🐛 Bug Fixes
- Fixed timer accuracy issues
- Improved notification reliability
- Better error handling
- Enhanced stability

---

**Built with ❤️ for productivity enthusiasts worldwide!**

For support, documentation, and source code, visit our [GitHub repository](https://github.com/ahmelkholy/ultimate-focus-timer).
"""

        release_notes_file = self.root_dir / f"release_notes_v{version}.md"
        with open(release_notes_file, 'w') as f:
            f.write(notes)

        print(f"✅ Release notes created: {release_notes_file}")
        return release_notes_file

    def create_release_tag(self, version):
        """Create and push Git tag for release"""
        try:
            # Check if we're in a git repository
            subprocess.run(["git", "status"], check=True, capture_output=True)

            # Add all changes
            subprocess.run(["git", "add", "."], cwd=self.root_dir, check=True)

            # Commit changes
            commit_msg = f"Release v{version}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=self.root_dir, check=True)

            # Create tag
            tag_msg = f"Ultimate Focus Timer v{version}"
            subprocess.run(["git", "tag", "-a", f"v{version}", "-m", tag_msg], cwd=self.root_dir, check=True)

            print(f"✅ Git tag v{version} created")
            print("📤 To push the release, run: git push origin main --tags")
            return True

        except subprocess.CalledProcessError:
            print("⚠️ Git operations failed - you may need to create the tag manually")
            return False

    def full_release(self, version_type="patch", auto_build=True):
        """Perform full release process"""
        print("🚀 Starting full release process...")
        print("=" * 50)

        # Bump version
        new_version = self.bump_version(version_type)

        # Update changelog
        self.update_changelog(new_version)

        # Build executable if requested
        if auto_build:
            if not self.build_executable():
                print("❌ Build failed, aborting release")
                return False

        # Create release notes
        self.create_github_release_notes(new_version)

        # Create git tag
        self.create_release_tag(new_version)

        print("\n🎉 Release process completed!")
        print(f"📋 Version: {new_version}")
        print("📁 Check the 'dist' folder for built executables")
        print("📝 Release notes created")
        print("📤 Push with: git push origin main --tags")

        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ultimate Focus Timer Release Manager")

    parser.add_argument(
        "action",
        choices=["bump", "build", "notes", "tag", "full"],
        help="Action to perform"
    )

    parser.add_argument(
        "--type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Version bump type (default: patch)"
    )

    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building executable in full release"
    )

    args = parser.parse_args()

    manager = ReleaseManager()

    if args.action == "bump":
        manager.bump_version(args.type)
    elif args.action == "build":
        manager.build_executable()
    elif args.action == "notes":
        version = manager.get_current_version()
        manager.create_github_release_notes(version)
    elif args.action == "tag":
        version = manager.get_current_version()
        manager.create_release_tag(version)
    elif args.action == "full":
        manager.full_release(args.type, not args.no_build)

if __name__ == "__main__":
    main()
