#!/usr/bin/env python3
"""
Plays the iconic Taco Bell bong sound

# /// script
# dependencies = ["pygame>=2.0.0"]
# ///
"""

import os
import pygame
import sys


def main():
    """Play the Taco Bell bong sound effect"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sound_file = os.path.join(script_dir, "taco-bell-bong-sfx.mp3")
    
    if not os.path.exists(sound_file):
        print(f"Error: Sound file not found: {sound_file}")
        return 1
    
    try:
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load and play the sound
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()
        
        # Wait for the sound to finish
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
            
        print("Taco Bell bong played successfully!")
        return 0
        
    except Exception as e:
        print(f"Error playing sound: {e}")
        # Fallback to system beep
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            print("Played system beep as fallback")
            return 0
        except Exception:
            print("Could not play any sound")
            return 1


if __name__ == "__main__":
    sys.exit(main())