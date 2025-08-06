#!/usr/bin/env python3
"""
Explosion overlay using Windows layered window with transparency
"""

import ctypes
import os
import sys
import threading
import subprocess
from pathlib import Path
import pygame
import cv2
import numpy as np

# Windows API constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x8
LWA_ALPHA = 0x2
LWA_COLORKEY = 0x1

# Windows API functions
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

def play_explosion_overlay():
    """Display transparent explosion overlay"""
    
    # Handle PyInstaller bundled files
    if hasattr(sys, '_MEIPASS'):
        # Running as executable - PyInstaller temp directory
        script_dir = Path(sys._MEIPASS)
    else:
        # Running as script
        script_dir = Path(__file__).parent
    
    video_file = script_dir / "Explosion.mp4"
    
    if not video_file.exists():
        return False
    
    # Play audio using FFplay in background
    def play_audio():
        try:
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", str(video_file)
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    # Start audio playback
    audio_thread = threading.Thread(target=play_audio)
    audio_thread.daemon = True
    audio_thread.start()
    
    # Initialize pygame
    pygame.init()
    
    # Get primary monitor dimensions
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    # Set display to primary monitor
    os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
    
    # Create pygame surface but don't show yet
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME | pygame.HIDDEN)
    pygame.display.set_caption("")  # No title
    
    # Get window handle
    hwnd = pygame.display.get_wm_info()["window"]
    
    # Make window layered, topmost, and remove from taskbar BEFORE showing
    current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_LAYERED | WS_EX_TOPMOST | 0x80)  # WS_EX_TOOLWINDOW
    
    # Set color key to make black pixels transparent BEFORE showing
    user32.SetLayeredWindowAttributes(hwnd, 0x000000, 255, LWA_COLORKEY)
    
    # Fill screen with black (transparent)
    screen.fill((0, 0, 0))
    
    # Now show the window
    user32.ShowWindow(hwnd, 5)  # SW_SHOW
    
    # Force window to be always on top - use multiple approaches
    user32.SetWindowPos(hwnd, -1, 0, 0, screen_width, screen_height, 0x0010)  # HWND_TOPMOST, SWP_SHOWWINDOW
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    
    pygame.display.flip()
    
    # Open video with OpenCV - set buffer size to 1 for speed
    cap = cv2.VideoCapture(str(video_file))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        pygame.quit()
        return False
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    clock = pygame.time.Clock()
    
    try:
        running = True
        frame_count = 0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        while running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Convert green screen to black (for transparency)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower_green = np.array([40, 40, 40])
            upper_green = np.array([80, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            frame[mask > 0] = [0, 0, 0]  # Set green pixels to black
            
            # Resize to screen
            frame = cv2.resize(frame, (screen_width, screen_height))
            
            # Convert to pygame surface
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            # Draw to screen
            screen.blit(frame_surface, (0, 0))
            pygame.display.flip()
            
            # Keep window on top every few frames
            if frame_count % 10 == 0:
                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_TOPMOST
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    running = False
            
            # Maintain FPS
            clock.tick(fps)
            
    except Exception as e:
        pass
    finally:
        cap.release()
        pygame.quit()
    
    return True

if __name__ == "__main__":
    play_explosion_overlay()