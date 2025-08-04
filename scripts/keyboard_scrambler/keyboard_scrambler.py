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
    # Get random keys to press
    keys_to_press = get_random_keys()
    
    # Give user a moment before starting
    time.sleep(1)
    
    # Press each key with random delays
    for key in keys_to_press:
        try:
            # Random delay between key presses (0.05 to 0.3 seconds)
            delay = random.uniform(0.05, 0.3)
            time.sleep(delay)
            
            # Handle special key combinations
            if key in ['shift', 'ctrl', 'alt']:
                # For modifier keys, press and hold briefly
                pyautogui.keyDown(key)
                time.sleep(0.1)
                pyautogui.keyUp(key)
            else:
                # Regular key press
                pyautogui.press(key)
                
        except Exception:
            continue


def main():
    """Main keyboard scrambler function"""
    try:
        scramble_keyboard()
    except:
        pass


if __name__ == "__main__":
    main()