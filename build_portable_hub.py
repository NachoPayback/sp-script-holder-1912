#!/usr/bin/env python3
"""
Build script to create portable hub executable with all dependencies bundled
"""

import subprocess
import sys
from pathlib import Path

def build_portable_hub():
    """Build portable hub.exe with all dependencies"""
    
    print("Building portable hub with all dependencies...")
    
    # Get paths
    project_root = Path(__file__).parent
    hub_script = project_root / "v2" / "hub" / "hub.py"
    scripts_dir = project_root / "scripts"
    config_dir = project_root / "v2" / "config"
    
    # Verify paths exist
    if not hub_script.exists():
        print(f"Error: Hub script not found at {hub_script}")
        return False
    
    if not scripts_dir.exists():
        print(f"Error: Scripts directory not found at {scripts_dir}")
        return False
        
    if not config_dir.exists():
        print(f"Error: Config directory not found at {config_dir}")  
        return False
    
    # All dependencies found in scripts analysis
    hidden_imports = [
        # Core hub dependencies
        "supabase",
        "supabase._async.client",
        
        # Script dependencies
        "pygame",              # taco_bell_bong
        "selenium",            # browser_tab_chaos
        "selenium.webdriver",
        "selenium.webdriver.chrome.options",
        "win32com.client",     # change_desktop_icons
        "pyautogui",           # move_mouse, minimize_windows
        "requests",            # youtube_wallpaper_prank
        "rotatescreen",        # screen_rotation_prank
        "winsound",            # play_sound (built-in, but include just in case)
        
        # Windows API dependencies  
        "ctypes",
        "winreg",
        
        # Standard library that sometimes needs explicit inclusion
        "subprocess",
        "threading",
        "asyncio",
        "json",
        "hashlib",
        "platform",
        "socket",
        "random",
        "time",
        "datetime",
    ]
    
    # Build PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                                    # Single executable
        "--name", "sp-crew-hub",                       # Output name
        "--distpath", str(project_root / "dist"),      # Output directory
        "--workpath", str(project_root / "build"),     # Build directory
        "--specpath", str(project_root),               # Spec file location
        
        # Add data files
        f"--add-data={scripts_dir};scripts",           # Include scripts
        f"--add-data={config_dir};config",             # Include config
        
        # Console application (not windowed)
        "--console",
        
        # Clean build
        "--clean",
        
        # Include all hidden imports
        *[f"--hidden-import={module}" for module in hidden_imports],
        
        # Source file
        str(hub_script)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"This will create: {project_root / 'dist' / 'sp-crew-hub.exe'}")
    print("Expected size: ~80-120MB (includes Python runtime + all dependencies)")
    print()
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=project_root, check=True)
        
        # Check if output exists
        output_file = project_root / "dist" / "sp-crew-hub.exe"
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"\nSUCCESS!")
            print(f"Portable hub created: {output_file}")
            print(f"Size: {size_mb:.1f} MB")
            print(f"\nTo deploy:")
            print(f"1. Copy {output_file.name} to any Windows machine")
            print(f"2. Run it - no Python installation required!")
            print(f"3. It includes all {len(hidden_imports)} dependencies")
            return True
        else:
            print(f"\nBuild completed but output file not found: {output_file}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\nPyInstaller failed with return code {e.returncode}")
        return False
    except Exception as e:
        print(f"\nBuild failed: {e}")
        return False

if __name__ == "__main__":
    print("SP Crew Control - Portable Hub Builder")
    print("=" * 50)
    
    # Check if PyInstaller is available
    try:
        subprocess.run(["pyinstaller", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)
    
    if build_portable_hub():
        print("\nPortable hub ready for deployment!")
    else:
        print("\nBuild failed - check output above")
        sys.exit(1)