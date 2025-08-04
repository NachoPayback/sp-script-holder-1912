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


class FakeProgressDialog:
    def __init__(self, title, message, total_time=8):
        self.title = title
        self.message = message
        self.total_time = total_time
        self.root = None
        self.progress_var = None
        self.status_var = None
        self.running = True
        
    def create_dialog(self):
        """Create the progress dialog window"""
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("450x180")
        self.root.resizable(False, False)
        
        # Make it look like a system dialog
        self.root.configure(bg='white')
        
        # Position randomly on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Random position but ensure dialog stays on screen
        x = random.randint(50, max(50, screen_width - 500))
        y = random.randint(50, max(50, screen_height - 230))
        self.root.geometry(f"450x180+{x}+{y}")
        
        # Keep window on top
        self.root.attributes('-topmost', True)
        
        # Add Windows-style icon (if available)
        try:
            self.root.iconbitmap(default="")
        except:
            pass
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title label
        title_label = tk.Label(main_frame, text=self.title, 
                              font=('Segoe UI', 11, 'bold'),
                              bg='white', fg='#000080')
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Message label
        message_label = tk.Label(main_frame, text=self.message,
                                font=('Segoe UI', 9),
                                bg='white', fg='black',
                                wraplength=400, justify='left')
        message_label.pack(anchor='w', pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                     maximum=100, length=380,
                                     style='TProgressbar')
        progress_bar.pack(pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Initializing...")
        status_label = tk.Label(main_frame, textvariable=self.status_var,
                               font=('Segoe UI', 8),
                               bg='white', fg='#666666')
        status_label.pack(anchor='w')
        
        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        return self.root
    
    def update_progress(self):
        """Update progress bar and status"""
        statuses = [
            "Scanning system files...",
            "Optimizing registry entries...",
            "Defragmenting memory...",
            "Cleaning temporary files...",
            "Updating system cache...",
            "Verifying system integrity...",
            "Optimizing startup programs...",
            "Compacting databases...",
            "Analyzing disk usage...",
            "Rebuilding file indexes...",
            "Clearing browser cache...",
            "Optimizing network settings...",
            "Updating driver cache...",
            "Finalizing optimization..."
        ]
        
        steps = len(statuses)
        step_duration = self.total_time / steps
        
        for i, status in enumerate(statuses):
            if not self.running:
                break
                
            progress = (i + 1) * (100 / steps)
            self.progress_var.set(progress)
            self.status_var.set(status)
            self.root.update()
            
            # Variable sleep time for realistic progress
            sleep_time = step_duration * random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        
        # Show completion
        if self.running:
            self.progress_var.set(100)
            self.status_var.set("Optimization complete!")
            self.root.update()
            time.sleep(1)
    
    def run(self):
        """Run the fake progress dialog"""
        self.create_dialog()
        
        # Start progress update in a separate thread
        progress_thread = threading.Thread(target=self.update_progress)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Show dialog
        self.root.mainloop()
    
    def close(self):
        """Close the dialog"""
        self.running = False
        if self.root:
            self.root.destroy()


def create_single_progress_dialog():
    """Create one random progress dialog"""
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
    
    # Choose one random dialog
    selected_dialog = random.choice(dialog_types)
    
    # Random duration between 3-7 seconds
    duration = random.randint(3, 7)
    
    print(f"🔄 FAKE PROGRESS BAR ACTIVATED!")
    print(f"📊 Dialog: {selected_dialog['title']}")
    print(f"⏰ Duration: {duration} seconds")
    print("=" * 45)
    
    dialog = FakeProgressDialog(
        selected_dialog["title"],
        selected_dialog["message"],
        duration
    )
    
    print("🚨 Showing fake progress dialog...")
    dialog.run()
    
    print("✅ Fake progress dialog completed!")
    print("🎭 Hope that looked convincingly official!")


def main():
    """Main fake progress bars function"""
    try:
        # Hide console window on Windows
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        
        create_single_progress_dialog()
        
    except KeyboardInterrupt:
        print("\n🛑 Fake progress bars interrupted by user")
    except Exception as e:
        print(f"❌ Error creating fake progress bars: {e}")
        print("💡 Make sure tkinter is available on your system")


if __name__ == "__main__":
    main()