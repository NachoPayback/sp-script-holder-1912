#!/usr/bin/env python3
"""
Plays the iconic Taco Bell bong sound
"""

import os
import subprocess
import sys

def play_taco_bell_bong():
    """Play the Taco Bell bong sound using the MP3 file"""
    try:
        # Get the directory where the script is located (same folder as audio file)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        audio_file = os.path.join(script_dir, "taco-bell-bong-sfx.mp3")
        
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Play the MP3 file using Windows Media Player
        subprocess.run([
            "powershell", "-Command", 
            f"Add-Type -AssemblyName presentationCore; " +
            f"$mediaPlayer = New-Object system.windows.media.mediaplayer; " +
            f"$mediaPlayer.open([uri]'{audio_file}'); " +
            f"$mediaPlayer.Play(); " +
            f"Start-Sleep -Seconds 3"
        ], check=True, capture_output=True)
        
        return True
        
    except Exception as e:
        # Fallback to system sound if MP3 playback fails
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            pass
        return False

if __name__ == "__main__":
    play_taco_bell_bong()