#!/usr/bin/env python3
"""
Keyboard Scrambler - Randomly hits 2-15 keyboard keys
"""

import random
import time
import sys

try:
    import pyautogui
except ImportError:
    print("Installing required dependency: pyautogui")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui"])
    import pyautogui

# Disable pyautogui failsafe for this script
pyautogui.FAILSAFE = False


def get_random_keys():
    """Get a list of random keys to press"""
    # Common keyboard keys that are safe to press
    safe_keys = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        'space', 'backspace', 'enter',
        'left', 'right', 'up', 'down',
        'shift', 'ctrl', 'alt',
        'tab', 'capslock',
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        'home', 'end', 'pageup', 'pagedown',
        'insert', 'delete',
        ',', '.', '/', ';', "'", '[', ']', '\\',
        '`', '-', '='
    ]
    
    # Determine random number of keys to press (2-15)
    num_keys = random.randint(2, 15)
    
    # Select random keys
    selected_keys = random.choices(safe_keys, k=num_keys)
    
    return selected_keys


def scramble_keyboard():
    """Execute the keyboard scrambling"""
    print("⌨️ KEYBOARD SCRAMBLER ACTIVATED!")
    print("=" * 40)
    
    # Get random keys to press
    keys_to_press = get_random_keys()
    
    print(f"🎯 Will press {len(keys_to_press)} random keys")
    print(f"🔑 Keys: {', '.join(keys_to_press)}")
    print()
    
    # Give user a moment to see what's happening
    print("🚨 Starting keyboard chaos in 2 seconds...")
    time.sleep(2)
    
    print("⌨️ SCRAMBLING KEYBOARD NOW!")
    
    # Press each key with random delays
    for i, key in enumerate(keys_to_press, 1):
        try:
            # Random delay between key presses (0.05 to 0.3 seconds)
            delay = random.uniform(0.05, 0.3)
            time.sleep(delay)
            
            # Press the key
            print(f"   [{i}/{len(keys_to_press)}] Pressing: {key}")
            
            # Handle special key combinations
            if key in ['shift', 'ctrl', 'alt']:
                # For modifier keys, press and hold briefly
                pyautogui.keyDown(key)
                time.sleep(0.1)
                pyautogui.keyUp(key)
            else:
                # Regular key press
                pyautogui.press(key)
                
        except Exception as e:
            print(f"   ⚠ Failed to press {key}: {e}")
            continue
    
    print()
    print("✅ KEYBOARD SCRAMBLING COMPLETE!")
    print("🎉 Hope that caused some entertaining chaos!")


def main():
    """Main keyboard scrambler function"""
    try:
        scramble_keyboard()
    except KeyboardInterrupt:
        print("\n🛑 Keyboard scrambler interrupted by user")
    except Exception as e:
        print(f"❌ Error during keyboard scrambling: {e}")
        print("💡 Make sure no security software is blocking key simulation")


if __name__ == "__main__":
    main()