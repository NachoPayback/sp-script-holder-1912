#!/usr/bin/env python3
"""
Screen Rotation Prank - Rotates screen briefly then restores
"""

import time


def reset_screen_to_default():
    """Emergency reset - force screen back to normal orientation"""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # Reset to default display settings (restores orientation to 0)
        result = user32.ChangeDisplaySettingsW(None, 0)
        print("Screen reset to default orientation")
        return True
    except Exception as e:
        print(f"Could not reset screen: {e}")
    return False


def main():
    """Main prank function"""
    import sys

    # Check for reset command
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("RESET MODE: Forcing screen back to default...")
        if reset_screen_to_default():
            print("Screen reset complete!")
        else:
            print("Reset failed - try manually in Display Settings")
        return

    print("Screen Rotation Prank starting...")

    try:
        # Use Windows API directly instead of rotatescreen package
        import ctypes
        from ctypes import wintypes
        
        # Windows constants for display settings
        CDS_UPDATEREGISTRY = 0x00000001
        CDS_RESET = 0x40000000
        DISP_CHANGE_SUCCESSFUL = 0
        
        # Display orientation constants  
        DMDO_DEFAULT = 0
        DMDO_90 = 1
        DMDO_180 = 2
        DMDO_270 = 3
        
        # Get current display settings
        user32 = ctypes.windll.user32
        
        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ('dmDeviceName', ctypes.c_char * 32),
                ('dmSpecVersion', wintypes.WORD),
                ('dmDriverVersion', wintypes.WORD),
                ('dmSize', wintypes.WORD),
                ('dmDriverExtra', wintypes.WORD),
                ('dmFields', wintypes.DWORD),
                ('dmOrientation', ctypes.c_short),
                ('dmPaperSize', ctypes.c_short),
                ('dmPaperLength', ctypes.c_short),
                ('dmPaperWidth', ctypes.c_short),
                ('dmScale', ctypes.c_short),
                ('dmCopies', ctypes.c_short),
                ('dmDefaultSource', ctypes.c_short),
                ('dmPrintQuality', ctypes.c_short),
                ('dmColor', ctypes.c_short),
                ('dmDuplex', ctypes.c_short),
                ('dmYResolution', ctypes.c_short),
                ('dmTTOption', ctypes.c_short),
                ('dmCollate', ctypes.c_short),
                ('dmFormName', ctypes.c_char * 32),
                ('dmLogPixels', wintypes.WORD),
                ('dmBitsPerPel', wintypes.DWORD),
                ('dmPelsWidth', wintypes.DWORD),
                ('dmPelsHeight', wintypes.DWORD),
                ('dmDisplayFlags', wintypes.DWORD),
                ('dmDisplayFrequency', wintypes.DWORD),
                ('dmICMMethod', wintypes.DWORD),
                ('dmICMIntent', wintypes.DWORD),
                ('dmMediaType', wintypes.DWORD),
                ('dmDitherType', wintypes.DWORD),
                ('dmReserved1', wintypes.DWORD),
                ('dmReserved2', wintypes.DWORD),
                ('dmPanningWidth', wintypes.DWORD),
                ('dmPanningHeight', wintypes.DWORD),
                ('dmDisplayOrientation', wintypes.DWORD),
                ('dmDisplayFixedOutput', wintypes.DWORD),
            ]

        # Get current display settings
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)
        
        if not user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dm)):
            print("Could not get current display settings")
            return
            
        original_orientation = dm.dmDisplayOrientation
        original_width = dm.dmPelsWidth
        original_height = dm.dmPelsHeight
        print(f"Original orientation: {original_orientation}")

        # Random rotation sequence (2-4 rotations)
        import random
        rotations = [DMDO_90, DMDO_180, DMDO_270]
        num_rotations = random.randint(2, 4)
        rotation_sequence = random.choices(rotations, k=num_rotations)
        
        print(f"Starting {num_rotations} random rotations...")
        
        for i, rotation in enumerate(rotation_sequence, 1):
            print(f"Rotation {i}/{num_rotations}: {rotation * 90} degrees...")
            
            # Set rotation and adjust dimensions
            dm.dmDisplayOrientation = rotation
            if rotation in [DMDO_90, DMDO_270]:  # Portrait orientations
                dm.dmPelsWidth = original_height
                dm.dmPelsHeight = original_width
            else:  # Landscape orientations (0, 180)
                dm.dmPelsWidth = original_width
                dm.dmPelsHeight = original_height
            
            result = user32.ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
            if result != DISP_CHANGE_SUCCESSFUL:
                print(f"Failed rotation {i}: {result}")
                break
                
            # Random pause between rotations (1-3 seconds)
            pause = random.uniform(1.0, 3.0)
            time.sleep(pause)

        print("Rotation sequence complete! Restoring original in 2 seconds...")
        time.sleep(2)

        # Restore original settings
        dm.dmDisplayOrientation = original_orientation
        dm.dmPelsWidth = original_width
        dm.dmPelsHeight = original_height
        
        print("Restoring original orientation...")
        user32.ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
        
        print("Screen rotation prank complete!")

    except Exception as e:
        print(f"Error during screen rotation: {e}")
        try:
            # Try to reset display settings
            user32 = ctypes.windll.user32
            user32.ChangeDisplaySettingsW(None, 0)
            print("Attempted to restore display settings")
        except Exception:
            print("Could not restore orientation automatically")
            print("You may need to manually fix screen orientation in Display Settings")


if __name__ == "__main__":
    main()
