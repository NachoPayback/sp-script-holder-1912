#!/usr/bin/env python3
"""
Simple desktop icon prank - changes shortcut icons to W logo
"""

import time
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("win32com not available - this script requires Windows")
    exit(1)


def main():
    """Main prank function"""
    print("Starting desktop icon prank...")

    # Get icon path
    icon_path = Path(__file__).parent / "W_Logo1.ico"
    if not icon_path.exists():
        print("W_Logo1.ico not found in scripts folder")
        return

    # Get desktop shortcuts
    desktop = Path.home() / "Desktop"
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcuts = list(desktop.glob("*.lnk"))

    print(f"Found {len(shortcuts)} shortcuts")

    # Backup and change icons
    originals = {}
    for lnk in shortcuts:
        try:
            shortcut = shell.CreateShortCut(str(lnk))
            # Store both icon location and target for better restoration
            originals[str(lnk)] = {
                'icon': shortcut.IconLocation,
                'target': shortcut.Targetpath
            }
            shortcut.IconLocation = str(icon_path)
            shortcut.save()
            print(f"Changed: {lnk.name}")
        except Exception as e:
            print(f"Failed {lnk.name}: {e}")

    # Force Windows to refresh desktop
    import ctypes
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)

    print(f"Changed {len(originals)} icons. Restoring in 10 seconds...")
    time.sleep(10)

    # Restore icons
    for lnk_path, backup in originals.items():
        try:
            shortcut = shell.CreateShortCut(lnk_path)
            # If no original icon, reset to use target executable's icon
            if not backup['icon'] or backup['icon'] == ',0':
                shortcut.IconLocation = backup['target'] + ",0"
            else:
                shortcut.IconLocation = backup['icon']
            shortcut.save()
        except Exception:
            pass

    # Force refresh again
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)

    print("Done!")


if __name__ == "__main__":
    main()
