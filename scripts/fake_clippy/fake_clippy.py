#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fake Clippy - Brings back the "helpful" Microsoft Office Assistant
"""

import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import sys
import math
import base64
import io
import os
from PIL import Image, ImageTk


class FakeClippy:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.clippy_image = None
        self.running = True
        self.start_time = None
        
        # Get Clippy image as base64
        self.clippy_base64 = self.get_clippy_base64()
        
    def get_clippy_base64(self):
        """Get the embedded Clippy image as base64"""
        try:
            clippy_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Clippy.png')
            with open(clippy_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"Could not load Clippy image: {e}")
            return ""
    
    def load_clippy_image(self):
        """Load Clippy image from base64"""
        if not self.clippy_base64:
            return None
            
        try:
            image_data = base64.b64decode(self.clippy_base64)
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error loading Clippy image: {e}")
            return None
        
    def get_random_message(self):
        """Get a random Clippy-style message"""
        messages = [
            "It looks like you're trying to work.\nWould you like help procrastinating?",
            "I see you're using your computer.\nHave you tried turning it off and on again?",
            "It appears you're being productive.\nWould you like me to fix that?",
            "Looks like you're typing.\nDid you know I can make this much more difficult?",
            "I notice you haven't clicked on me in a while.\nAre you ignoring me?",
            "It seems like you're focused.\nWould you like some distractions?",
            "I see you're working efficiently.\nThis simply won't do!",
            "Are you trying to get things done?\nI'm here to help make that impossible!",
            "It looks like you're in the zone.\nTime for an interruption!",
            "I noticed you're being successful.\nWould you like me to change that?",
            "Looks like you're having a good day.\nI can fix that for you!",
            "I see you're not using Internet Explorer.\nThis concerns me greatly.",
            "It appears you're happy with your current setup.\nI disagree.",
            "Are you trying to avoid me?\nBecause that's not going to work.",
            "I think you need more paperclips in your life.\nDon't you agree?",
            "Looks like you're trying to be professional.\nWould you like help with that?",
            "I see you're working hard.\nHave you considered working hardly instead?",
            "It appears you know what you're doing.\nThat's unfortunate.",
            "Are you sure you want to do that?\nBecause I'm not.",
            "I notice you're trying to concentrate.\nThat seems boring."
        ]
        return random.choice(messages)
    
    def create_window(self):
        """Create a borderless, transparent Clippy window"""
        self.root = tk.Tk()
        
        # Remove window decorations (no title bar, borders)
        self.root.overrideredirect(True)
        
        # Make window transparent
        self.root.attributes('-transparentcolor', '#000001')  # Use a color we won't use
        self.root.configure(bg='#000001')
        
        # Set window size
        window_width = 400
        window_height = 300
        
        # Position randomly on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = random.randint(50, max(50, screen_width - window_width - 50))
        y = random.randint(50, max(50, screen_height - window_height - 50))
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Keep window on top
        self.root.attributes('-topmost', True)
        
        # Load Clippy image
        self.clippy_image = self.load_clippy_image()
        
        # Create canvas with transparent background
        self.canvas = tk.Canvas(self.root, width=window_width, height=window_height, 
                               bg='#000001', highlightthickness=0, bd=0)
        self.canvas.pack()
        
        return self.root
    
    def draw_speech_bubble(self, message, x=50, y=30):
        """Draw speech bubble with message"""
        # Calculate bubble size based on text
        bubble_width = 280
        bubble_height = 100
        
        # Speech bubble background (classic yellow)
        bubble = self.canvas.create_rectangle(x, y, x + bubble_width, y + bubble_height, 
                                            fill='#FFFFCC', outline='#000000', width=2)
        
        # Speech bubble pointer (pointing to Clippy)
        pointer_x = x + bubble_width - 50
        pointer_y = y + bubble_height
        pointer = self.canvas.create_polygon(
            pointer_x, pointer_y,
            pointer_x + 20, pointer_y + 30,
            pointer_x + 40, pointer_y,
            fill='#FFFFCC', outline='#000000', width=2
        )
        
        # Add text to bubble
        text_x = x + bubble_width // 2
        text_y = y + bubble_height // 2
        
        text = self.canvas.create_text(text_x, text_y, text=message, 
                                     font=('MS Sans Serif', 9, 'normal'), 
                                     justify='center', width=bubble_width - 20,
                                     fill='#000000')
        
        return [bubble, pointer, text]
    
    def draw_clippy(self, x=250, y=170, bounce_offset=0):
        """Draw Clippy image"""
        actual_y = y + bounce_offset
        
        if self.clippy_image:
            return self.canvas.create_image(x, actual_y, image=self.clippy_image, anchor='center')
        else:
            # Fallback: simple paperclip shape
            items = []
            # Main paperclip body
            items.append(self.canvas.create_oval(x-30, actual_y-40, x+30, actual_y+40, 
                                               outline='#4169E1', width=4, fill=''))
            # Eyes
            items.append(self.canvas.create_oval(x-10, actual_y-15, x-5, actual_y-10, fill='black'))
            items.append(self.canvas.create_oval(x+5, actual_y-15, x+10, actual_y-10, fill='black'))
            # Smile
            items.append(self.canvas.create_arc(x-15, actual_y-5, x+15, actual_y+10, 
                                              start=200, extent=140, outline='black', width=2))
            return items
    
    def animate_and_show(self):
        """Main animation loop with auto-close"""
        message = self.get_random_message()
        
        # Draw speech bubble
        bubble_items = self.draw_speech_bubble(message)
        
        # Animation loop
        self.start_time = time.time()
        animation_duration = 6.0  # 6 seconds
        
        clippy_item = None
        
        while self.running and (time.time() - self.start_time) < animation_duration:
            try:
                # Calculate bounce
                elapsed = time.time() - self.start_time
                bounce_offset = int(10 * math.sin(elapsed * 4))  # Bouncing motion
                
                # Remove old Clippy
                if clippy_item:
                    if isinstance(clippy_item, list):
                        for item in clippy_item:
                            self.canvas.delete(item)
                    else:
                        self.canvas.delete(clippy_item)
                
                # Draw new Clippy position
                clippy_item = self.draw_clippy(bounce_offset=bounce_offset)
                
                # Update display
                self.root.update()
                time.sleep(0.05)  # ~20 FPS
                
            except tk.TclError:
                # Window was closed
                break
            except Exception as e:
                print(f"Animation error: {e}")
                break
        
        # Close window
        self.close()
    
    def show_clippy(self):
        """Show Clippy with message and animation"""
        try:
            self.create_window()
            
            # Start animation in main thread (tkinter needs this)
            self.animate_and_show()
            
        except Exception as e:
            print(f"Error showing Clippy: {e}")
            self.close()
    
    def close(self):
        """Close Clippy window"""
        self.running = False
        if self.root:
            try:
                self.root.destroy()
            except:
                pass


def main():
    """Main fake Clippy function"""
    # Fix Unicode encoding for console output
    if sys.platform == "win32":
        # Set console to UTF-8 encoding
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass
        
        # Hide console window
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    try:
        print("📎 CLIPPY IS BACK!")
        print("=" * 30)
        print("💡 The 'helpful' Office Assistant returns...")
        
        # Create and show Clippy
        clippy = FakeClippy()
        clippy.show_clippy()
        
        print("✅ Clippy appearance complete!")
        print("📎 Hope that brought back some memories!")
        
    except KeyboardInterrupt:
        print("\n🛑 Clippy interrupted by user")
    except Exception as e:
        print(f"❌ Error showing Clippy: {e}")
        print("💡 Make sure tkinter and PIL are available on your system")


if __name__ == "__main__":
    main()