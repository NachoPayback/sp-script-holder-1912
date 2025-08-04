#!/usr/bin/env python3
"""
Fake Progress Bars - Shows convincing fake system maintenance dialogs
"""

import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import sys
import os


def create_progress_dialog():
    """Create a fake progress dialog that auto-closes"""
    
    dialog_types = [
        {
            "title": "System Optimizer",
            "message": "Windows is optimizing your system for better performance. This may take a few moments..."
        },
        {
            "title": "Disk Cleanup Utility", 
            "message": "Cleaning unnecessary files and optimizing disk space. Please do not turn off your computer."
        },
        {
            "title": "Registry Cleaner",
            "message": "Scanning and repairing registry entries to improve system stability..."
        },
        {
            "title": "Memory Optimizer",
            "message": "Optimizing system memory and clearing unused processes. This will improve performance."
        },
        {
            "title": "Windows Update Assistant",
            "message": "Preparing system updates and installing critical patches. Please wait..."
        },
        {
            "title": "Security Scan",
            "message": "Running comprehensive security scan to detect and remove potential threats..."
        },
        {
            "title": "System Maintenance",
            "message": "Performing scheduled maintenance tasks to keep your system running smoothly."
        }
    ]
    
    selected_dialog = random.choice(dialog_types)
    duration = random.randint(3, 7)
    
    # Create the window
    root = tk.Tk()
    root.title(selected_dialog["title"])
    root.geometry("450x180")
    root.resizable(False, False)
    root.configure(bg='white')
    
    # Position randomly
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = random.randint(50, max(50, screen_width - 500))
    y = random.randint(50, max(50, screen_height - 230))
    root.geometry(f"450x180+{x}+{y}")
    
    # Keep on top and prevent closing
    root.attributes('-topmost', True)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Main frame
    main_frame = tk.Frame(root, bg='white', padx=20, pady=20)
    main_frame.pack(fill='both', expand=True)
    
    # Title
    title_label = tk.Label(main_frame, text=selected_dialog["title"], 
                          font=('Segoe UI', 11, 'bold'),
                          bg='white', fg='#000080')
    title_label.pack(anchor='w', pady=(0, 10))
    
    # Message
    message_label = tk.Label(main_frame, text=selected_dialog["message"],
                            font=('Segoe UI', 9), bg='white', fg='black',
                            wraplength=400, justify='left')
    message_label.pack(anchor='w', pady=(0, 15))
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(main_frame, variable=progress_var,
                                 maximum=100, length=380)
    progress_bar.pack(pady=(0, 10))
    
    # Status
    status_var = tk.StringVar()
    status_var.set("Initializing...")
    status_label = tk.Label(main_frame, textvariable=status_var,
                           font=('Segoe UI', 8), bg='white', fg='#666666')
    status_label.pack(anchor='w')
    
    # Status messages
    statuses = [
        "Scanning system files...",
        "Optimizing registry entries...", 
        "Defragmenting memory...",
        "Cleaning temporary files...",
        "Updating system cache...",
        "Verifying system integrity...",
        "Finalizing optimization..."
    ]
    
    # Animation function
    def animate():
        steps = len(statuses)
        step_duration = duration / steps
        
        for i, status in enumerate(statuses):
            if not root.winfo_exists():
                return
                
            try:
                progress = (i + 1) * (100 / steps)
                progress_var.set(progress)
                status_var.set(status)
                root.update()
                time.sleep(step_duration * random.uniform(0.5, 1.5))
            except:
                return
        
        # Complete
        try:
            if root.winfo_exists():
                progress_var.set(100)
                status_var.set("Optimization complete!")
                root.update()
                time.sleep(0.5)
        except:
            pass
        
        # Force close
        try:
            root.quit()
            root.destroy()
        except:
            pass
    
    # Start animation thread
    animation_thread = threading.Thread(target=animate, daemon=True)
    animation_thread.start()
    
    # Emergency close after duration + buffer
    def emergency_close():
        try:
            if root.winfo_exists():
                root.quit()
                root.destroy()
        except:
            pass
    
    # Multiple close timers for reliability
    root.after(int((duration + 2) * 1000), emergency_close)
    root.after(int((duration + 3) * 1000), lambda: os._exit(0))
    
    # Show dialog
    try:
        root.mainloop()
    except:
        pass
    
    # Final cleanup
    try:
        root.destroy()
    except:
        pass


def main():
    """Main function"""
    # Hide console on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    try:
        create_progress_dialog()
    except:
        pass
    
    # Force exit
    os._exit(0)


if __name__ == "__main__":
    main()