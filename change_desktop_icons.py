#!/usr/bin/env python3
"""
Temporarily changes all desktop shortcut icons to W logo
"""

import os
import time
import tempfile
from pathlib import Path
import win32com.client

def create_w_icon():
    """Create a temporary W icon file"""
    # Get the W logo from the project directory
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    w_logo_path = os.path.join(script_dir, "W_Logo1.png")
    
    # For now, we'll use the PNG directly (Windows can handle PNG icons in shortcuts)
    temp_icon = os.path.join(tempfile.gettempdir(), "w_icon.png")
    
    # Copy the W logo to temp location
    import shutil
    shutil.copy2(w_logo_path, temp_icon)
    return temp_icon

def change_desktop_icons():
    """Temporarily change all desktop shortcut icons to W logo"""
    shell = win32com.client.Dispatch("WScript.Shell")
    desktop_path = shell.SpecialFolders("Desktop")
    
    # Create W icon
    w_icon = create_w_icon()
    
    # Store original icons
    original_icons = {}
    
    try:
        # Find all .lnk files on desktop
        for filename in os.listdir(desktop_path):
            if filename.endswith('.lnk'):
                shortcut_path = os.path.join(desktop_path, filename)
                try:
                    shortcut = shell.CreateShortCut(shortcut_path)
                    # Save original icon
                    original_icons[shortcut_path] = shortcut.IconLocation
                    # Set W icon
                    shortcut.IconLocation = f"{w_icon},0"
                    shortcut.Save()
                except Exception as e:
                    print(f"Couldn't change {filename}: {e}")
        
        print(f"Changed {len(original_icons)} desktop icons to W logo!")
        
        # Wait 10 seconds
        time.sleep(10)
        
        # Restore original icons
        for shortcut_path, original_icon in original_icons.items():
            try:
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.IconLocation = original_icon
                shortcut.Save()
            except Exception:
                pass
        
        print("Desktop icons restored!")
        
    finally:
        # Clean up temp icon
        try:
            os.remove(w_icon)
        except Exception:
            pass

if __name__ == "__main__":
    change_desktop_icons()