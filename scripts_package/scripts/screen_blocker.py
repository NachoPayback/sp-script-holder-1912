#!/usr/bin/env python3
"""
Screen Blocker - Creates a random colored block that covers part of the screen
"""

import tkinter as tk
import random
import time
import threading


def create_screen_block():
    """Create a random colored block that covers part of the screen"""
    
    # Create main window
    root = tk.Tk()
    
    # Remove window decorations and make it stay on top
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Random block size (200-600 pixels wide/tall)
    block_width = random.randint(200, 600)
    block_height = random.randint(200, 600)
    
    # Random position on screen (ensure it stays visible)
    max_x = screen_width - block_width
    max_y = screen_height - block_height
    block_x = random.randint(0, max(0, max_x))
    block_y = random.randint(0, max(0, max_y))
    
    # Set window geometry
    root.geometry(f"{block_width}x{block_height}+{block_x}+{block_y}")
    
    # Random bright color
    colors = [
        '#FF0000',  # Red
        '#00FF00',  # Green
        '#0000FF',  # Blue
        '#FFFF00',  # Yellow
        '#FF00FF',  # Magenta
        '#00FFFF',  # Cyan
        '#FFA500',  # Orange
        '#800080',  # Purple
        '#FFC0CB',  # Pink
        '#FFB6C1',  # Light Pink
        '#98FB98',  # Pale Green
        '#87CEEB',  # Sky Blue
    ]
    
    random_color = random.choice(colors)
    root.configure(bg=random_color)
    
    # No text - just solid color block
    
    # Prevent window from being closed easily
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Auto-close after 10-15 seconds
    duration = random.randint(10, 15)
    
    def auto_close():
        time.sleep(duration)
        try:
            root.quit()
            root.destroy()
        except:
            pass
    
    # Start auto-close timer
    timer_thread = threading.Thread(target=auto_close, daemon=True)
    timer_thread.start()
    
    # Make it slightly transparent so it's more annoying than completely blocking
    root.attributes('-alpha', 0.9)  # 90% opacity
    
    print(f"Screen blocker active at ({block_x}, {block_y}) - {block_width}x{block_height}")
    print(f"Color: {random_color}")
    print(f"Auto-closing in {duration} seconds...")
    
    try:
        root.mainloop()
    except:
        pass
    
    print("Screen blocker closed!")


def main():
    """Main entry point for the script"""
    print("Creating screen blocker...")
    create_screen_block()


if __name__ == "__main__":
    main()