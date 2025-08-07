#!/usr/bin/env python3
"""
Screen Rotation Prank - Rotates screen briefly then restores
"""

import time


def reset_screen_to_default():
    """Emergency reset - force screen back to normal orientation"""
    try:
        import rotatescreen
        screen = rotatescreen.get_primary_display()
        if screen is not None:
            screen.rotate_to(0)  # 0 = normal orientation
            print("Screen reset to default orientation (0 degrees)")
            return True
        else:
            print("Could not get primary display")
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
        # Import the rotate-screen package
        import rotatescreen
        import random

        # Get the primary display
        screen = rotatescreen.get_primary_display()
        if screen is None:
            print("Could not get primary display")
            return
            
        print(f"Found display: {screen}")

        # Get current orientation
        original_orientation = screen.current_orientation
        print(f"Original orientation: {original_orientation}")

        # Pick random rotation angle manually
        import os
        random_bytes = os.urandom(1)[0]  # Get truly random byte
        random_choice = random_bytes % 3  # 0, 1, or 2
        
        if random_choice == 0:
            random_angle = 90
        elif random_choice == 1:
            random_angle = 180
        else:
            random_angle = 270
        
        print(f"DEBUG: Random choice: {random_choice}")
        print(f"DEBUG: Selected angle: {random_angle}")
        print(f"Rotating screen {random_angle} degrees...")
        screen.rotate_to(random_angle)
        
        # Check what orientation we actually got
        actual_orientation = screen.current_orientation
        print(f"DEBUG: After rotation, actual orientation is: {actual_orientation}")

        print("Screen rotated! Restoring in 5 seconds...")
        time.sleep(5)

        # Restore original orientation
        print("Restoring original orientation...")
        screen.rotate_to(original_orientation)
        
        # Verify restoration
        final_orientation = screen.current_orientation
        print(f"DEBUG: After restore, final orientation is: {final_orientation}")

        print("Screen rotation prank complete!")

    except ImportError:
        print("Error: rotate-screen package not installed")
        print("Please install with: pip install rotate-screen")
        return
    except Exception as e:
        print(f"Error during screen rotation: {e}")
        try:
            # Try to restore to normal orientation if something went wrong
            if reset_screen_to_default():
                print("Attempted to restore to normal orientation")
        except Exception:
            print("Could not restore orientation automatically")
            print("You may need to manually fix screen orientation in Display Settings")


if __name__ == "__main__":
    main()
