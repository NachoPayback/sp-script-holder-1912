#!/usr/bin/env python3
"""
Randomly moves the mouse cursor in large increments
"""

import time
import random
import pyautogui

# Disable pyautogui failsafe (moving mouse to corner won't stop script)
pyautogui.FAILSAFE = False

def move_mouse_randomly():
    """Randomly adjusts the mouse cursor position for 10 seconds"""
    
    try:
        print("Starting mouse cursor adjustment...")
        
        # Get current mouse position
        original_x, original_y = pyautogui.position()
        
        # Duration of adjustment (10 seconds)
        end_time = time.time() + 10
        
        while time.time() < end_time:
            # Get current position
            current_x, current_y = pyautogui.position()
            
            # Random HUGE movements (200-600 pixels)
            move_x = random.randint(-600, 600)
            move_y = random.randint(-600, 600)
            
            # Move mouse smoothly but faster
            pyautogui.moveRel(move_x, move_y, duration=0.05)
            
            # Small pause
            time.sleep(0.2)
        
        # Move back to near original position
        pyautogui.moveTo(original_x, original_y, duration=0.5)
        
        print("Mouse cursor adjustment completed!")
        return True
        
    except Exception as e:
        print(f"Error during mouse movement: {e}")
        return False

if __name__ == "__main__":
    move_mouse_randomly()