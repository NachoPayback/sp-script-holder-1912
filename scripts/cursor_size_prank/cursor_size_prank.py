#!/usr/bin/env python3
"""
Cursor Size Chaos - Temporarily changes cursor size to giant then restores
"""

import time

try:
    import ctypes
    import winreg
except ImportError:
    print("This script requires Windows")
    exit(1)


def get_current_cursor_size():
    """Get current cursor size from registry"""
    try:
        # Check CursorSize in Accessibility settings
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Accessibility",
                            0, winreg.KEY_READ)
        try:
            cursor_size, _ = winreg.QueryValueEx(key, "CursorSize")
            winreg.CloseKey(key)
            return cursor_size
        except FileNotFoundError:
            winreg.CloseKey(key)
            return 1  # Default size
    except Exception:
        return 1  # Default if we can't read


def get_current_cursor_base_size():
    """Get current cursor base size from registry"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Control Panel\Cursors",
                            0, winreg.KEY_READ)
        try:
            base_size, _ = winreg.QueryValueEx(key, "CursorBaseSize")
            winreg.CloseKey(key)
            return base_size
        except FileNotFoundError:
            winreg.CloseKey(key)
            return 32  # Default base size
    except Exception:
        return 32  # Default if we can't read


def set_cursor_size(size):
    """
    Set cursor size (1-15 where 1=32px, 2=48px, etc. in steps of 16px)
    """
    try:
        # Calculate base size (32 + (size-1) * 16)
        base_size = 32 + (size - 1) * 16

        # Ensure Accessibility key exists
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Accessibility",
                               0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
            # Create the key if it doesn't exist
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Accessibility")

        # Set CursorSize
        winreg.SetValueEx(key, "CursorSize", 0, winreg.REG_DWORD, size)
        winreg.CloseKey(key)

        # Set CursorBaseSize in Control Panel\Cursors
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Control Panel\Cursors",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "CursorBaseSize", 0, winreg.REG_DWORD, base_size)
        winreg.CloseKey(key)

        # Force immediate cursor reload with multiple API calls
        SPI_SETCURSORS = 0x0057
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        
        # Call SystemParametersInfo to reload cursors
        result1 = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETCURSORS,
            0,
            None,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        # Force cursor cache refresh
        ctypes.windll.user32.SetSystemCursor(0, 32512)  # OCR_NORMAL
        
        # Additional refresh calls
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        
        # Force desktop refresh
        ctypes.windll.user32.InvalidateRect(0, None, True)
        ctypes.windll.user32.UpdateWindow(0)
        
        result = result1

        if result:
            print(f"Cursor size changed to {size} (base size: {base_size}px)")
            return True
        else:
            print("Failed to reload cursors")
            return False

    except Exception as e:
        print(f"Error setting cursor size: {e}")
        return False


def reset_cursor_to_default():
    """Emergency reset - force cursor back to default size"""
    try:
        print("Resetting cursor to default size (1 = 32px)...")
        if set_cursor_size(1):  # Default size is 1 (32px)
            print("Cursor reset to default size!")
            return True
        else:
            print("Failed to reset cursor size")
            return False
    except Exception as e:
        print(f"Error resetting cursor: {e}")
        return False


def main():
    """Main prank function"""
    import sys

    # Check for reset command
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("RESET MODE: Forcing cursor back to default...")
        if reset_cursor_to_default():
            print("Cursor reset complete!")
        else:
            print("Reset failed - try manually in Settings > Accessibility > Mouse pointer")
        return

    print("Cursor Size Chaos starting...")

    # Get original cursor settings
    original_size = get_current_cursor_size()
    original_base_size = get_current_cursor_base_size()

    print(f"Original cursor size: {original_size} (base: {original_base_size}px)")

    # Set giant cursor size (size 8 = 32 + 7*16 = 144px)
    giant_size = 8
    print(f"Setting cursor to giant size ({giant_size})...")

    if set_cursor_size(giant_size):
        print("Giant cursor activated! Restoring in 6 seconds...")
        time.sleep(6)

        # Restore original size
        print("Restoring original cursor size...")
        if set_cursor_size(original_size):
            print("Original cursor size restored!")
        else:
            print("Warning: Could not restore cursor size automatically")
            print("You may need to adjust cursor size manually in Settings > Accessibility")
    else:
        print("Failed to change cursor size")

    print("Cursor size chaos complete!")


if __name__ == "__main__":
    main()
