#!/usr/bin/env python3
"""
Build script for SP Crew Hub V3
Builds both silent and terminal versions
"""

import os
import sys
import subprocess
from pathlib import Path

def build_hub_exe(silent=True):
    """Build hub executable"""
    project_root = Path(__file__).parent
    hub_dir = project_root / "hub"
    
    # Source file and exe name
    source_file = hub_dir / "sp_crew_hub.py"
    exe_name = "SP-Crew-Hub-Silent" if silent else "SP-Crew-Hub-Terminal"
    console = not silent
    
    if not source_file.exists():
        print(f"ERROR: Source file not found: {source_file}")
        return False
    
    print(f"Building {'Silent' if silent else 'Terminal'} Hub V3...")
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", exe_name,
        "--console" if console else "--windowed",
        "--hidden-import", "supabase",
        "--hidden-import", "rich",
        "--hidden-import", "keyboard", 
        "--hidden-import", "certifi",
        "--hidden-import", "requests",
        "--clean",
        "--noconfirm",
        "--log-level", "WARN",
        str(source_file)
    ]
    
    # Add data files including the new bundled program sync
    cmd.extend([
        "--add-data", f"{hub_dir / 'program_sync_bundled.py'}:.",
        "--add-data", f"{hub_dir / 'program_sync.py'}:."  # Keep old one as fallback
    ])
    
    print(f"Running PyInstaller...")
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = project_root / "dist" / f"{exe_name}.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024*1024)
            print(f"SUCCESS: {exe_name}.exe ({size_mb:.1f} MB)")
            return True
    
    print(f"BUILD FAILED:")
    print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
    print("STDERR:", result.stderr[-500:] if result.stderr else "None")
    return False

def main():
    """Build both versions"""
    print("=== SP CREW HUB V3 BUILD ===")
    
    # Install dependencies first
    hub_dir = Path(__file__).parent / "hub"
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(hub_dir)], 
                  capture_output=True)
    
    # Build both versions
    silent_ok = build_hub_exe(silent=True)
    terminal_ok = build_hub_exe(silent=False)
    
    print("\n=== BUILD SUMMARY ===")
    print(f"Silent Hub: {'OK' if silent_ok else 'FAIL'}")
    print(f"Terminal Hub: {'OK' if terminal_ok else 'FAIL'}")
    
    return silent_ok and terminal_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)