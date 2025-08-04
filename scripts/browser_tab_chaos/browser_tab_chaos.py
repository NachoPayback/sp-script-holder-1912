#!/usr/bin/env python3
"""
Browser Tab Chaos - Opens 3 Chrome tabs
"""

import subprocess
import time


def main():
    """Open 3 Chrome tabs using command line"""
    print("Browser Tab Chaos starting...")
    
    # Just open blank tabs
    urls = [
        "about:blank",
        "about:blank", 
        "about:blank"
    ]
    
    try:
        # Try to find Chrome
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        ]
        
        chrome_exe = None
        for path in chrome_paths:
            expanded_path = subprocess.run(["cmd", "/c", f"echo {path}"], 
                                         capture_output=True, text=True).stdout.strip()
            try:
                # Test if Chrome exists at this path
                subprocess.run([expanded_path, "--version"], 
                             capture_output=True, check=True)
                chrome_exe = expanded_path
                break
            except:
                continue
        
        if not chrome_exe:
            print("Chrome not found, trying default browser...")
            # Use start command to open with default browser
            for url in urls:
                subprocess.run(["cmd", "/c", f"start {url}"], shell=True)
                time.sleep(0.5)
        else:
            print(f"Found Chrome at: {chrome_exe}")
            # Open all URLs in Chrome
            # First URL opens normally, others open as new tabs
            subprocess.Popen([chrome_exe, urls[0]])
            time.sleep(1)  # Wait for Chrome to start
            
            for url in urls[1:]:
                subprocess.Popen([chrome_exe, "--new-tab", url])
                time.sleep(0.5)
        
        print("Opened 3 browser tabs successfully!")
        
    except Exception as e:
        print(f"Error opening browser tabs: {e}")


if __name__ == "__main__":
    main()