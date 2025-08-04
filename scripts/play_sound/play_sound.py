#!/usr/bin/env python3
"""
Plays a random Windows system sound effect
"""

import random
import winsound


def play_random_sound():
    """Play a random Windows system sound that catches attention"""
    # List of attention-grabbing Windows system sounds
    sounds = [
        "SystemHand",          # Critical Stop - very attention-grabbing
        "SystemExclamation",   # Windows Error - makes people think something's wrong
        "SystemQuestion",      # Question sound - curious
        "SystemStart",         # Windows startup sound - confusing
        "SystemExit",          # Windows shutdown sound - alarming
        "SystemAsterisk",      # Asterisk/Info sound
    ]
    
    # Additional sounds that are more subtle but confusing
    subtle_sounds = [
        "*",                   # Default beep
        "SystemDefault",       # System default
    ]
    
    # Combine all sounds, but weight the attention-grabbing ones more heavily
    all_sounds = sounds + sounds + subtle_sounds  # Double the main sounds for higher probability
    
    # Pick a random sound
    sound = random.choice(all_sounds)
    
    try:
        # Play the sound with different flags for variety
        if sound in ["SystemHand", "SystemExclamation"]:
            # Play critical sounds asynchronously so they don't block
            winsound.PlaySound(sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            # Play other sounds synchronously
            winsound.PlaySound(sound, winsound.SND_ALIAS)
            
        print(f"Played attention-grabbing sound: {sound}")
        return True
    except Exception as e:
        print(f"Error playing sound: {e}")
        # Fallback to simple beep if all else fails
        try:
            winsound.Beep(800, 300)  # 800Hz for 300ms - distinctive beep
            print("Played fallback beep sound")
            return True
        except:
            print("Could not play any sound")
            return False

if __name__ == "__main__":
    play_random_sound()
