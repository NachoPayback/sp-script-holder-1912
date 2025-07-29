#!/usr/bin/env python3
"""
Build script for P_Buttons Hub executable
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    """Build hub.exe with PyInstaller"""
    print("[BUILD] Building P_Buttons Hub...")
    
    # Clean previous builds
    build_dir = Path("build")
    dist_dir = Path("dist")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller command for hub  
    cmd = [
        "uv", "run", "pyinstaller",
        "--onefile",
        "--noconsole",  # Run without console window
        "--distpath", "dist_hub",
        "--name", "hub",
        "--icon", "scripts/W_Logo1.ico",
        "--add-data", "config;config",
        "--add-data", "scripts;scripts", 
        "--hidden-import", "nats",
        "--hidden-import", "pynput",
        "--hidden-import", "GitPython",
        "--hidden-import", "pyautogui",
        "--hidden-import", "pywin32",
        "--hidden-import", "flask",
        "src/hub.py"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        # Copy to main dist folder
        Path("dist").mkdir(exist_ok=True)
        shutil.copy("dist_hub/hub.exe", "dist/hub.exe")
        print("[SUCCESS] hub.exe built successfully!")
        print("Location: dist/hub.exe")
    else:
        print("[ERROR] Build failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())