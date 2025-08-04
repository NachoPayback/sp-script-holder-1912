#!/usr/bin/env python3
"""
Explosion overlay using Windows API for true transparency
"""

import tkinter as tk
import threading
import subprocess
import glob
import time
from pathlib import Path
import win32gui
import win32con

def play_explosion_overlay():
    """Display explosion overlay with true transparency"""
    
    script_dir = Path(__file__).parent
    audio_file = script_dir / "explosion_audio.mp3"
    frames_dir = script_dir / "frames"
    
    print("Starting transparent explosion overlay...")
    
    # Get all frame files
    frame_files = sorted(glob.glob(str(frames_dir / "frame_*.png")))
    
    if not frame_files:
        print("ERROR: No PNG frames found")
        return False
    
    print(f"Using {len(frame_files)} frames")
    
    # Create window
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Position and size window
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.configure(bg='black')
    
    # Create canvas
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, 
                      bg='black', highlightthickness=0)
    canvas.pack()
    
    # Get window handle after it's created
    root.update()
    hwnd = int(root.wm_frame(), 16)
    
    # Make window layered and click-through
    try:
        # Set window as layered
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                              win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | 
                              win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
        
        # Set black as transparent color
        win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 0, win32con.LWA_COLORKEY)
        
        print("Window transparency enabled")
        
    except Exception as e:
        print(f"Transparency setup failed: {e}")
    
    # Load and scale frames
    frames = []
    print("Loading and scaling frames...")
    
    try:
        from PIL import Image, ImageTk
        print("Using PIL for scaling...")
        
        for i, frame_file in enumerate(frame_files):
            try:
                # Load with PIL and scale to screen size
                pil_img = Image.open(frame_file)
                # Scale to fill screen
                pil_img = pil_img.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(pil_img)
                frames.append(img)
                
                if i % 20 == 0:
                    print(f"Loaded {i+1}/{len(frame_files)} frames...")
                    
            except Exception as e:
                print(f"Failed to load {frame_file}: {e}")
                break
        
        print(f"Loaded {len(frames)} frames")
        
    except ImportError:
        print("PIL not available - using tkinter fallback")
        # Fallback to tkinter without scaling
        for i, frame_file in enumerate(frame_files):
            try:
                img = tk.PhotoImage(file=frame_file)
                frames.append(img)
                
                if i % 20 == 0:
                    print(f"Loaded {i+1}/{len(frame_files)} frames...")
                    
            except Exception as e:
                print(f"Failed to load {frame_file}: {e}")
                break
        
        print(f"Loaded {len(frames)} frames")
        
    except Exception as e:
        print(f"Frame loading failed: {e}")
        return False
    
    if not frames:
        return False
    
    # Start audio and video simultaneously
    def play_audio():
        try:
            if audio_file.exists():
                subprocess.run([
                    "powershell", "-c", 
                    "Add-Type -AssemblyName presentationCore; " +
                    "$player = New-Object System.Windows.Media.MediaPlayer; " +
                    f"$player.Open([System.Uri]::new('{audio_file.as_uri()}')); " +
                    "$player.Play(); " +
                    "Start-Sleep -Seconds 5; " +
                    "$player.Close()"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            print(f"Audio failed: {e}")
    
    # Start audio immediately
    audio_thread = threading.Thread(target=play_audio, daemon=True)
    audio_thread.start()
    
    # Animation
    current_frame = 0
    start_time = time.time()
    
    def animate():
        nonlocal current_frame
        
        if current_frame < len(frames):
            canvas.delete("all")
            # Draw scaled image at top-left to fill screen
            canvas.create_image(0, 0, anchor='nw', image=frames[current_frame])
            current_frame += 1
            # 24fps = ~42ms per frame
            root.after(42, animate)
        else:
            total_time = time.time() - start_time
            print(f"Animation completed in {total_time:.2f}s")
            root.destroy()
    
    print("Starting synchronized playback...")
    animate()
    
    # Auto-close after 6 seconds
    root.after(6000, root.destroy)
    
    try:
        root.mainloop()
        return True
    except Exception as e:
        print(f"Overlay error: {e}")
        return False

if __name__ == "__main__":
    success = play_explosion_overlay()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")