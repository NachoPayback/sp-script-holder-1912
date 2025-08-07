#!/usr/bin/env python3
"""
Minimizes all open windows temporarily then restores them
"""

import subprocess
import time


def minimize_restore_windows():
    """Minimize all windows then restore them after 5 seconds"""

    try:
        print("Minimizing all windows...")

        # Method 1: Use Windows+D shortcut to show desktop
        # This is reversible with another Windows+D
        import pyautogui

        # Press Windows+D to minimize all
        pyautogui.hotkey('win', 'd')

        print("All windows minimized! Waiting 5 seconds...")

        # Wait 5 seconds
        time.sleep(5)

        # Press Windows+D again to restore
        pyautogui.hotkey('win', 'd')

        print("Windows restored!")
        return True

    except Exception as e:
        print(f"Error during window operation: {e}")

        # Backup method using PowerShell
        try:
            restore_cmd = '''
            (New-Object -ComObject Shell.Application).UndoMinimizeAll()
            '''
            subprocess.run(["powershell", "-Command", restore_cmd], timeout=2)
            print("Windows restored using backup method")
        except Exception:
            pass

        return False

def main():
    """Main entry point for the script"""
    import sys
    success = minimize_restore_windows()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
