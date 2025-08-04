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
    print("Installing required dependency: psutil")
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
    
    print("🎵 Opening Rick Roll video...")
    
    try:
        # Open Chrome with the Rick Roll URL
        process = subprocess.Popen([
            chrome_path,
            "--new-window",
            "--start-maximized",
            url
        ])
        
        print(f"✅ Rick Roll opened! Process ID: {process.pid}")
        return process
        
    except Exception as e:
        print(f"❌ Failed to open Chrome: {e}")
        print("💡 Trying default browser...")
        
        # Fallback: Use default browser
        try:
            import webbrowser
            webbrowser.open(url)
            print("✅ Opened in default browser")
            return None  # Can't track process for default browser
        except Exception as e2:
            print(f"❌ Failed to open default browser: {e2}")
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
                        print(f"🔇 Closing Chrome process {proc.info['pid']} with Rick Roll...")
                        proc.terminate()
                        closed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        print(f"⚠ Error closing Chrome tabs: {e}")
    
    # Alternative method: Close newest Chrome window
    if closed_count == 0:
        try:
            print("🔇 Attempting to close newest Chrome window...")
            subprocess.run([
                "taskkill", "/F", "/IM", "chrome.exe", "/T"
            ], capture_output=True)
            print("✅ Chrome processes terminated")
        except Exception as e:
            print(f"⚠ Could not force close Chrome: {e}")
    
    return closed_count


def main():
    """Main Rick Roll prank function"""
    print("🎭 RICK ROLL PRANK ACTIVATED!")
    print("=" * 40)
    
    # Random duration between 3-5 seconds
    duration = random.randint(3, 5)
    print(f"⏰ Rick Roll will play for {duration} seconds")
    
    # Open the Rick Roll
    chrome_process = open_rickroll()
    
    if chrome_process is None:
        print("⚠ Could not track Chrome process, using timer only...")
    
    # Wait for the specified duration
    print(f"🎵 Rick Rolling in progress...")
    for i in range(duration, 0, -1):
        print(f"   Closing in {i} seconds... 🎶", end="\r")
        time.sleep(1)
    print()
    
    # Close the Rick Roll
    print("🔇 Time's up! Closing Rick Roll...")
    
    if chrome_process:
        try:
            chrome_process.terminate()
            print("✅ Chrome process terminated")
        except:
            print("⚠ Could not terminate specific process, trying alternative...")
            close_chrome_tabs_with_rickroll()
    else:
        close_chrome_tabs_with_rickroll()
    
    print()
    print("🎉 RICK ROLL PRANK COMPLETE!")
    print("🎵 Never gonna give you up, never gonna let you down! 🎵")
    print("😄 Hope you enjoyed the surprise!")


if __name__ == "__main__":
    import os
    main()