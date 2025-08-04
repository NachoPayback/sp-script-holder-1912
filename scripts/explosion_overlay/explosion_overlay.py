#!/usr/bin/env python3
"""
Explosion overlay using PNG sequence with transparency
"""

import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import winsound
from pathlib import Path
import glob

def play_explosion_overlay():
    """Display explosion overlay with perfect transparency"""
    
    script_dir = Path(__file__).parent
    audio_file = script_dir / "explosion_audio.mp3"
    frames_dir = script_dir / "frames"
    
    # Get all PNG frames from frames folder
    frame_files = sorted(glob.glob(str(frames_dir / "frame_*.png")))
    
    if not frame_files:
        print("ERROR: No PNG frames found")
        return False
    
    if not audio_file.exists():
        print("ERROR: Audio file not found")
        return False
    
    print(f"Found {len(frame_files)} frames and audio file")
    
    # Create fullscreen transparent window with 95% opacity
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.95)  # 95% opacity
    root.attributes('-transparentcolor', 'black')
    root.configure(bg='black')
    root.overrideredirect(True)
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Create label for displaying frames
    label = tk.Label(root, bg='black')
    label.place(x=0, y=0, width=screen_width, height=screen_height)
    
    # Load and resize all frames with enhanced screening effect
    frames = []
    for frame_file in frame_files:
        try:
            img = Image.open(frame_file)
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Enhance contrast and brightness for screen effect
            from PIL import ImageEnhance
            
            # Increase contrast for more punch
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(1.3)
            
            # Increase brightness slightly
            brightness = ImageEnhance.Brightness(img)
            img = brightness.enhance(1.1)
            
            # Increase saturation for more vivid colors
            saturation = ImageEnhance.Color(img)
            img = saturation.enhance(1.2)
            
            # Resize to screen while maintaining aspect ratio
            img = img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"Error loading frame {frame_file}: {e}")
    
    if not frames:
        print("ERROR: No frames could be loaded")
        root.destroy()
        return False
    
    print(f"Loaded {len(frames)} frames")
    
    # Play audio in separate thread
    def play_audio():
        try:
            # Use PowerShell to play MP3 (more reliable than winsound for MP3)
            import subprocess
            subprocess.run([
                "powershell", "-c", 
                f"Add-Type -AssemblyName presentationCore; " +
                f"$player = New-Object System.Windows.Media.MediaPlayer; " +
                f"$player.Open([System.Uri]::new('{audio_file.as_uri()}')); " +
                f"$player.Play(); " +
                f"Start-Sleep -Seconds 5; " +
                f"$player.Close()"
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    audio_thread = threading.Thread(target=play_audio, daemon=True)
    audio_thread.start()
    
    # Animation variables
    current_frame = 0
    frame_delay = 1000 // 30  # 30 FPS in milliseconds
    
    def update_frame():
        nonlocal current_frame
        if current_frame < len(frames):
            label.configure(image=frames[current_frame])
            current_frame += 1
            root.after(frame_delay, update_frame)
        else:
            # Animation finished, close window
            root.after(500, root.destroy)  # Small delay before closing
    
    # Start animation
    update_frame()
    
    # Auto-close failsafe (in case animation doesn't finish properly)
    root.after(8000, root.destroy)  # Close after 8 seconds max
    
    # Run the animation
    try:
        root.mainloop()
        print("Explosion overlay completed")
        return True
    except Exception as e:
        print(f"Overlay error: {e}")
        return False

if __name__ == "__main__":
    print("Starting explosion overlay...")
    success = play_explosion_overlay()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")