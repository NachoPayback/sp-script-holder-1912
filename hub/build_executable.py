#!/usr/bin/env python3
"""
Build script to create a standalone SP Crew Hub executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Build standalone executable using PyInstaller"""
    
    # Fix encoding for Windows console
    if sys.platform == "win32":
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except:
            pass
    
    # Get paths
    hub_dir = Path(__file__).parent
    project_root = hub_dir.parent
    scripts_dir = project_root / "scripts"
    config_dir = hub_dir / "config"
    
    print("Building SP Crew Hub Standalone Executable...")
    print(f"Hub directory: {hub_dir}")
    print(f"Scripts directory: {scripts_dir}")
    print(f"Config directory: {config_dir}")
    
    # Check if required files exist
    if not (hub_dir / "hub.py").exists():
        print("ERROR: hub.py not found!")
        return False
        
    if not config_dir.exists():
        print("ERROR: config directory not found!")
        return False
        
    if not scripts_dir.exists():
        print("ERROR: scripts directory not found!")
        return False
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable
        "--windowed",                   # No console window
        "--name", "SP-Crew-Hub",        # Executable name
        "--icon", "NONE",               # No icon for now
        "--add-data", f"{config_dir};config",           # Include config
        "--add-data", f"{scripts_dir};scripts",         # Include all scripts
        "--hidden-import", "supabase",
        "--hidden-import", "keyboard", 
        "--hidden-import", "rich",
        "--hidden-import", "git",
        "--collect-all", "supabase",
        "--collect-all", "keyboard",
        "--collect-all", "rich",
        "--collect-all", "git",
        "--collect-all", "gitdb",
        "--collect-all", "gitpython",
        str(hub_dir / "hub.py")
    ]
    
    print("Running PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=hub_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Build successful!")
            
            # Check if executable was created
            exe_path = hub_dir / "dist" / "SP-Crew-Hub.exe"
            if exe_path.exists():
                print(f"Executable created: {exe_path}")
                print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
                
                # Create a simple installer script
                create_installer_script(hub_dir, exe_path)
                
                return True
            else:
                print("ERROR: Executable not found in dist directory")
                return False
        else:
            print("Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error during build: {e}")
        return False

def create_installer_script(hub_dir, exe_path):
    """Create a simple installer/launcher script"""
    
    installer_content = f'''@echo off
title SP Crew Hub - Standalone Installation
echo.
echo ================================================
echo    SP CREW CONTROL HUB - STANDALONE INSTALLER
echo ================================================
echo.
echo This installer will set up SP Crew Hub on your computer.
echo No additional software installation required!
echo.
echo Features:
echo - Complete Python runtime included
echo - All dependencies bundled
echo - All prank scripts included  
echo - Emergency shutdown: Ctrl+Shift+Q
echo.
pause

echo.
echo Copying SP Crew Hub to Program Files...

if not exist "%ProgramFiles%\\SP-Crew-Hub" (
    mkdir "%ProgramFiles%\\SP-Crew-Hub"
)

copy "SP-Crew-Hub.exe" "%ProgramFiles%\\SP-Crew-Hub\\" >nul 2>&1

if %errorlevel% neq 0 (
    echo Failed to copy to Program Files. Trying current directory...
    echo.
    echo SP Crew Hub is ready to run from current directory!
    echo    Double-click SP-Crew-Hub.exe to start
) else (
    echo SP Crew Hub installed successfully!
    echo.
    echo To run SP Crew Hub:
    echo 1. Go to Start Menu ^> Run ^> %ProgramFiles%\\SP-Crew-Hub\\SP-Crew-Hub.exe
    echo 2. Or navigate to C:\\Program Files\\SP-Crew-Hub\\ and double-click SP-Crew-Hub.exe
)

echo.
echo EMERGENCY SHUTDOWN: Press Ctrl+Shift+Q while hub is running
echo.
echo Installation complete! 
pause
'''
    
    installer_path = hub_dir / "dist" / "Install-SP-Crew-Hub.bat"
    with open(installer_path, 'w') as f:
        f.write(installer_content)
    
    # Create a readme
    readme_content = '''SP CREW CONTROL HUB - STANDALONE VERSION
=====================================

INSTALLATION:
1. Run "Install-SP-Crew-Hub.bat" as Administrator (recommended)
   OR
2. Simply double-click "SP-Crew-Hub.exe" to run from current location

FEATURES:
- Complete standalone application (no Python installation needed)
- All prank scripts included and ready to use
- Connects to SP Crew Control remote interface
- Real-time script execution via Supabase

EMERGENCY SHUTDOWN:
Press Ctrl+Shift+Q at any time to immediately shut down the hub

SYSTEM REQUIREMENTS:
- Windows 10 or later
- Internet connection for remote commands
- ~100MB disk space

USAGE:
1. Run SP-Crew-Hub.exe
2. The hub will automatically connect and register
3. Use the web interface to send commands
4. Press Ctrl+Shift+Q to shutdown

For support, contact the SP Crew team.
'''
    
    readme_path = hub_dir / "dist" / "README.txt"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"Created installer: {installer_path}")
    print(f"Created readme: {readme_path}")

if __name__ == "__main__":
    success = main()
    if success:
        print("\nBuild completed successfully!")
        print("Check the 'dist' directory for your executable")
    else:
        print("\nBuild failed!")
    
    input("Press Enter to exit...")