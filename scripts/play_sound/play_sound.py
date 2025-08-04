#!/usr/bin/env python3
"""
Plays Windows system sounds - error, USB plugged/unplugged
"""

import random
import subprocess
import os

def play_random_sound():
    """Play a random Windows system sound (error or USB sounds)"""
    
    # Windows system sound files
    system_sounds = [
        # Error/Critical sounds
        r"C:\Windows\Media\Windows Critical Stop.wav",
        r"C:\Windows\Media\Windows Error.wav",
        r"C:\Windows\Media\Windows Exclamation.wav",
        # USB sounds
        r"C:\Windows\Media\Windows Hardware Insert.wav",
        r"C:\Windows\Media\Windows Hardware Remove.wav",
        r"C:\Windows\Media\Windows Hardware Fail.wav",
        # Device connect/disconnect
        r"C:\Windows\Media\DeviceConnect.wav",
        r"C:\Windows\Media\DeviceDisconnect.wav",
        r"C:\Windows\Media\DeviceFail.wav"
    ]
    
    # Filter to only existing files
    available_sounds = [s for s in system_sounds if os.path.exists(s)]
    
    if not available_sounds:
        print("No system sound files found, using fallback beep")
        # Fallback to PowerShell beep
        subprocess.run([
            "powershell", "-c", 
            "[console]::beep(800, 300)"
        ], capture_output=True)
        return True
    
    # Pick a random sound
    sound_file = random.choice(available_sounds)
    sound_name = os.path.basename(sound_file).replace('.wav', '')
    
    try:
        # Use PowerShell to play the sound
        ps_command = f'''
        Add-Type -TypeDefinition @"
        using System.Media;
        public class Sound {{
            public static void Play(string file) {{
                var player = new SoundPlayer(file);
                player.PlaySync();
            }}
        }}
"@
        [Sound]::Play("{sound_file}")
        '''
        
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print(f"Played sound: {sound_name}")
            return True
        else:
            # Fallback to simple PowerShell play
            subprocess.run([
                "powershell", "-c", 
                f'(New-Object Media.SoundPlayer "{sound_file}").PlaySync()'
            ], capture_output=True)
            print(f"Played sound (fallback): {sound_name}")
            return True
            
    except Exception as e:
        print(f"Error playing sound: {e}")
        # Final fallback beep
        subprocess.run([
            "powershell", "-c", 
            "[console]::beep(800, 300)"
        ], capture_output=True)
        return True

if __name__ == "__main__":
    play_random_sound()