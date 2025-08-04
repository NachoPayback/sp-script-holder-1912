#!/usr/bin/env python3
"""
Rick Roll Prank - Opens "Never Gonna Give You Up" for 3-5 seconds then closes it
"""

import subprocess
import time
import random
import sys

try:
    import psutil
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil


def get_chrome_executable():
    """Find Chrome executable path"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
            username=os.environ.get('USERNAME', '')
        )
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Try to find via registry
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        chrome_path, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        if os.path.exists(chrome_path):
            return chrome_path
    except:
        pass
    
    return "chrome"  # Hope it's in PATH


def open_rickroll():
    """Open Rick Roll video in Chrome"""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    chrome_path = get_chrome_executable()
    
    try:
        # Open Chrome with the Rick Roll URL
        process = subprocess.Popen([
            chrome_path,
            "--new-window",
            "--start-maximized",
            url
        ])
        
        return process
        
    except Exception as e:
        
        # Fallback: Use default browser
        try:
            import webbrowser
            webbrowser.open(url)
            return None  # Can't track process for default browser
        except Exception as e2:
            return None


def close_chrome_tabs_with_rickroll():
    """Close Chrome tabs containing the Rick Roll video"""
    closed_count = 0
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('dQw4w9WgXcQ' in str(arg) for arg in cmdline):
                        proc.terminate()
                        closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
    
    # Alternative method: Close newest Chrome window
    if closed_count == 0:
        try:
            subprocess.run([
                "taskkill", "/F", "/IM", "chrome.exe", "/T"
            ], capture_output=True)
        except Exception as e:
    
    return closed_count


def main():
    """Main Rick Roll prank function"""
    # Random duration between 3-5 seconds
    duration = random.randint(3, 5)
    
    # Open the Rick Roll
    chrome_process = open_rickroll()
    
    # Wait for the specified duration
    time.sleep(duration)
    
    # Close the Rick Roll
    if chrome_process:
        try:
            chrome_process.terminate()
            # Wait a moment then force close if needed
            time.sleep(0.5)
            if chrome_process.poll() is None:
                chrome_process.kill()
        except:
            close_chrome_tabs_with_rickroll()
    else:
        close_chrome_tabs_with_rickroll()


if __name__ == "__main__":
    import os
    main()