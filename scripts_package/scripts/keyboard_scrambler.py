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
    """Get a list of random typeable characters"""
    # Only typeable characters - letters, numbers, and symbols
    typeable_chars = [
        # Letters
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        # Numbers
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        # Symbols and punctuation
        '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',
        '[', ']', '{', '}', '\\', '|', ';', ':', "'", '"', ',', '.', '<', '>',
        '/', '?', '`', '~', ' '
    ]
    
    # Determine random number of keys to press (2-15)
    num_keys = random.randint(2, 15)
    
    # Select random characters
    selected_keys = random.choices(typeable_chars, k=num_keys)
    
    return selected_keys


def scramble_keyboard():
    """Execute the keyboard scrambling"""
    # Get random characters to type
    chars_to_type = get_random_keys()
    
    # Give user a moment before starting
    time.sleep(1)
    
    # Type each character with random delays
    for char in chars_to_type:
        try:
            # Random delay between key presses (0.05 to 0.3 seconds)
            delay = random.uniform(0.05, 0.3)
            time.sleep(delay)
            
            # Type the character directly
            pyautogui.write(char)
                
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