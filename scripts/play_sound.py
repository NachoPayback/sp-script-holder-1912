#!/usr/bin/env python3
"""
Plays a random Windows system sound effect
"""

import os
import random
import winsound

def play_random_sound():
    """Play a random Windows system sound"""
    # List of Windows system sounds
    sounds = [
        "SystemHand",      # Critical Stop
        "SystemQuestion",  # Question
        "SystemExclamation", # Exclamation
        "SystemAsterisk",  # Asterisk
        "SystemExit",      # Windows Exit
        "SystemStart",     # Windows Startup
    ]
    
    # Pick a random sound
    sound = random.choice(sounds)
    
    try:
        # Play the sound
        winsound.PlaySound(sound, winsound.SND_ALIAS)
        print(f"Played sound: {sound}")
        return True
    except Exception as e:
        print(f"Error playing sound: {e}")
        return False

if __name__ == "__main__":
    play_random_sound() 