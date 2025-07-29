#!/usr/bin/env python3
"""
Build script for P_Buttons Remote executable
"""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    """Build remote.exe with PyInstaller"""
    print("[BUILD] Building P_Buttons Remote...")
    
    # Clean previous builds
    build_dir = Path("build")
    dist_dir = Path("dist")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller command for remote
    cmd = [
        "uv", "run", "pyinstaller",
        "--onefile",
        "--distpath", "dist_remote",
        "--name", "remote",
        "--icon", "scripts/W_Logo1.ico",
        "--add-data", "src/remote/templates;templates",
        "--hidden-import", "nats",
        "--hidden-import", "flask",
        "src/remote/remote_app.py"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        # Copy to main dist folder
        Path("dist").mkdir(exist_ok=True)
        shutil.copy("dist_remote/remote.exe", "dist/remote.exe")
        print("[SUCCESS] remote.exe built successfully!")
        print("Location: dist/remote.exe")
        print("")
        print("Usage:")
        print("  remote.exe  - Starts web interface on http://127.0.0.1:5001")
    else:
        print("[ERROR] Build failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())