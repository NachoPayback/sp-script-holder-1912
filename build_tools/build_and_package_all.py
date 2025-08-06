#!/usr/bin/env python3
"""
Build and package everything for GitHub release
1. Build scripts.exe package
2. Build hub executables  
3. Copy to GitHub-ready structure
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def clean_dist():
    """Clean dist directory"""
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Cleaning dist directory...")
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(exist_ok=True)

def build_scripts():
    """Build scripts package"""
    print("\n=== BUILDING SCRIPTS PACKAGE ===")
    result = subprocess.run([sys.executable, "build_scripts_package.py"])
    return result.returncode == 0

def build_hubs():
    """Build hub executables"""
    print("\n=== BUILDING HUB EXECUTABLES ===")
    result = subprocess.run([sys.executable, "build_hub.py"])
    return result.returncode == 0

def prepare_github_release():
    """Prepare files for GitHub release"""
    print("\n=== PREPARING GITHUB RELEASE ===")
    
    dist_dir = Path("dist")
    
    # Check all required files exist
    required_files = [
        "scripts.exe",
        "version.json",
        "SP-Crew-Hub-Silent.exe",
        "SP-Crew-Hub-Terminal.exe"
    ]
    
    for file in required_files:
        if not (dist_dir / file).exists():
            print(f"ERROR: Missing {file}")
            return False
    
    # Create release info
    release_info = {
        "release": "SP Crew Bundle v1.0.0",
        "date": datetime.now().isoformat(),
        "contents": {
            "scripts.exe": "Bundled scripts package (all pranks in one)",
            "version.json": "Version info for scripts package",
            "SP-Crew-Hub-Silent.exe": "Silent hub (no console)",
            "SP-Crew-Hub-Terminal.exe": "Terminal hub (with console)"
        }
    }
    
    with open(dist_dir / "release_info.json", 'w') as f:
        json.dump(release_info, f, indent=2)
    
    print(f"Files ready in {dist_dir}:")
    for file in dist_dir.iterdir():
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({size_mb:.1f} MB)")
    
    return True

def main():
    """Main build process"""
    print("=== SP CREW COMPLETE BUILD ===")
    print("Building everything for fast script execution...")
    
    # Clean first
    clean_dist()
    
    # Build everything
    scripts_ok = build_scripts()
    if not scripts_ok:
        print("ERROR: Scripts build failed!")
        return 1
        
    hubs_ok = build_hubs()
    if not hubs_ok:
        print("ERROR: Hub build failed!")
        return 1
    
    # Prepare for GitHub
    release_ok = prepare_github_release()
    if not release_ok:
        print("ERROR: Release preparation failed!")
        return 1
    
    print("\n=== BUILD COMPLETE ===")
    print("All files ready in dist/ directory")
    print("\nNext steps:")
    print("1. Test the hub with: dist\\SP-Crew-Hub-Terminal.exe")
    print("2. Upload dist/ contents to GitHub")
    print("3. Hub will auto-download scripts.exe for fast execution!")
    
    return 0

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())