#!/usr/bin/env python3
"""Install a Finder/Dock launcher for this checkout; no login service is added."""

import plistlib
import shlex
import sys
from pathlib import Path


def main():
    if sys.platform != "darwin":
        raise SystemExit("This launcher is for macOS.")
    root = Path(__file__).resolve().parent.parent
    python = root / ".venv" / "bin" / "python"
    if not python.exists():
        raise SystemExit("Create the project's .venv before installing the launcher.")
    bundle = Path.home() / "Applications" / "Ultimate Focus.app"
    contents = bundle / "Contents"
    executable = contents / "MacOS" / "ultimate-focus"
    if bundle.exists():
        info_path = contents / "Info.plist"
        if (
            not info_path.exists()
            or plistlib.loads(info_path.read_bytes()).get("CFBundleIdentifier")
            != "local.ultimate-focus.launcher"
        ):
            raise SystemExit(f"An unrelated application already exists at {bundle}")
    executable.parent.mkdir(parents=True, exist_ok=True)
    # Generated paths are shell-quoted; nothing depends on Terminal's environment.
    executable.write_text(
        "#!/bin/sh\n"
        'export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"\n'
        f"cd {shlex.quote(str(root))} || exit 1\n"
        f"exec {shlex.quote(str(python))} {shlex.quote(str(root / 'focus_app.py'))}\n"
    )
    executable.chmod(0o755)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleName": "Ultimate Focus",
                "CFBundleDisplayName": "Ultimate Focus",
                "CFBundleIdentifier": "local.ultimate-focus.launcher",
                "CFBundleExecutable": "ultimate-focus",
                "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1",
                "NSHighResolutionCapable": True,
            }
        )
    )
    print(f"Installed {bundle}")


if __name__ == "__main__":
    main()
