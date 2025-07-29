#!/usr/bin/env python3
"""
Build both hub.exe and remote.exe
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Build both executables"""
    print("=== P_Buttons Build System ===\n")
    
    scripts = [
        ("Hub", "dev/build_hub.py"),
        ("Remote", "dev/build_remote.py")
    ]
    
    for name, script in scripts:
        print(f"Building {name}...")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"[ERROR] {name} build failed!")
            return 1
        print(f"[SUCCESS] {name} built\n")
    
    print("=== Build Complete ===")
    print("Files created:")
    print("  dist/hub.exe    - Deploy to target machines")  
    print("  dist/remote.exe - Run on control machines")
    print("")
    print("Ready for prank deployment! 🎯")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())