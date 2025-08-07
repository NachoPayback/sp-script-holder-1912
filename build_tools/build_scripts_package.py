#!/usr/bin/env python3
"""
Build SP Crew Scripts Package
Creates a single executable containing all scripts
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_scripts_exe():
    """Build the unified scripts executable"""
    project_root = Path(__file__).parent.parent  # Go up one level since we're in build_tools/
    package_dir = project_root / "scripts_package"
    
    if not package_dir.exists():
        print(f"ERROR: Package directory not found: {package_dir}")
        return False
    
    print("Building SP Crew Scripts Package...")
    print("This bundles ALL scripts into ONE fast-loading executable")
    
    # Create spec file content with all data files
    launcher_path = str(package_dir / "launcher.py").replace('\\', '\\\\')
    package_path = str(package_dir).replace('\\', '\\\\')
    scripts_path = str(package_dir / "scripts").replace('\\', '\\\\')
    assets_path = str(package_dir / "assets").replace('\\', '\\\\')
    registry_path = str(package_dir / "registry.py").replace('\\', '\\\\')
    assets_helper_path = str(package_dir / "assets_helper.py").replace('\\', '\\\\')
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['{launcher_path}'],
    pathex=['{package_path}'],
    binaries=[],
    datas=[
        ('{scripts_path}', 'scripts'),
        ('{assets_path}', 'assets'),
        ('{registry_path}', '.'),
        ('{assets_helper_path}', '.'),
    ],
    hiddenimports=[
        'pygame',
        'pyautogui', 
        'keyboard',
        'PIL',
        'screeninfo',
        'cv2',
        'numpy',
        'rotatescreen',
        'scripts.move_mouse',
        'scripts.taco_bell_bong',
        'scripts.rickroll_prank',
        'scripts.explosion_overlay',
        'scripts.fake_clippy',
        'scripts.change_desktop_icons',
        'scripts.color_filter_chaos',
        'scripts.fake_progress_bars',
        'scripts.fake_system_message',
        'scripts.keyboard_scrambler',
        'scripts.minimize_windows',
        'scripts.play_sound',
        'scripts.screen_rotation_prank',
        'scripts.system_maintenance',
        'scripts.youtube_wallpaper_prank',
        'scripts.lock_pc',
        'scripts.screen_blocker',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='scripts',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    # Write spec file
    spec_file = project_root / "scripts.spec"
    spec_file.write_text(spec_content)
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--log-level", "WARN",
        str(spec_file)
    ]
    
    print("Running PyInstaller...")
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = project_root / "dist" / "scripts.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024*1024)
            print(f"SUCCESS: scripts.exe built ({size_mb:.1f} MB)")
            print(f"Location: {exe_path}")
            
            # Create version file
            version_file = project_root / "dist" / "version.json"
            import json
            import hashlib
            
            # Calculate file hash
            with open(exe_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            version_data = {
                "version": "1.0.0",
                "hash": file_hash,
                "filename": "scripts.exe"
            }
            
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            print(f"Created version.json with hash: {file_hash[:8]}...")
            return True
    else:
        print(f"BUILD FAILED!")
        print("STDOUT:", result.stdout[-1000:] if result.stdout else "None")
        print("STDERR:", result.stderr[-1000:] if result.stderr else "None")
    
    return False

def main():
    """Main build process"""
    print("=== SP CREW SCRIPTS PACKAGE BUILD ===")
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                   "scripts_package/pyproject.toml"], capture_output=True)
    
    success = build_scripts_exe()
    
    if success:
        print("\n=== BUILD COMPLETE ===")
        print("The scripts.exe package is ready!")
        print("Hub can now download this single file instead of 15 separate executables")
        print("\nTo test: dist/scripts.exe --list")
        print("To run: dist/scripts.exe --run taco_bell_bong")
    else:
        print("\n=== BUILD FAILED ===")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())