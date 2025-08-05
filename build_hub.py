#!/usr/bin/env python3
"""
Single build script for SP Crew Hub
Builds both silent and terminal versions from portable-hub source
"""

import os
import sys
import subprocess
from pathlib import Path

def build_hub_exe(silent=True):
    """Build hub executable"""
    project_root = Path(__file__).parent
    hub_dir = project_root / "hub"
    portable_hub_dir = project_root / "portable-hub"
    
    # Choose source file and exe name
    if silent:
        source_file = portable_hub_dir / "portable_hub_silent.py"
        exe_name = "SP-Crew-Hub-Silent"
        console = False
    else:
        source_file = portable_hub_dir / "portable_hub.py"
        exe_name = "SP-Crew-Hub-Terminal"
        console = True
    
    # Ensure source exists
    if not source_file.exists():
        print(f"ERROR: Source file not found: {source_file}")
        return False
    
    print(f"Building {'Silent' if silent else 'Terminal'} Hub...")
    print(f"Source: {source_file}")
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", exe_name,
        "--console" if console else "--windowed",
        "--add-binary", f"{hub_dir / 'uv.exe'};.",
        "--add-data", f"{project_root / 'RickRoll_Small.mp4'};." if (project_root / 'RickRoll_Small.mp4').exists() else f"{project_root / 'RickRoll.mp4'};.",
        "--hidden-import", "supabase",
        "--hidden-import", "rich", 
        "--hidden-import", "keyboard",
        "--clean",
        str(source_file)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = project_root / "dist" / f"{exe_name}.exe"
        if exe_path.exists():
            print(f"SUCCESS: {exe_path}")
            print(f"Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
    
    print(f"BUILD FAILED:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    return False

def main():
    """Build both versions"""
    print("=== BUILDING SP CREW HUB EXECUTABLES ===")
    
    # Build silent version
    silent_ok = build_hub_exe(silent=True)
    print()
    
    # Build terminal version  
    terminal_ok = build_hub_exe(silent=False)
    
    print("\n=== BUILD SUMMARY ===")
    print(f"Silent Hub: {'✓' if silent_ok else '✗'}")
    print(f"Terminal Hub: {'✓' if terminal_ok else '✗'}")
    
    return silent_ok and terminal_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)