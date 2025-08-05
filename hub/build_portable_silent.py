#!/usr/bin/env python3
"""
Build script for silent portable SP Crew Hub
Creates a completely silent executable that runs in the background using portable_hub_silent.py
"""

import os
import sys
import subprocess
from pathlib import Path

def build_portable_silent():
    """Build silent portable hub executable"""
    project_root = Path(__file__).parent.parent
    hub_dir = Path(__file__).parent
    portable_hub_dir = project_root / "portable-hub"
    dist_dir = hub_dir / "dist"
    
    # Ensure dist directory exists
    dist_dir.mkdir(exist_ok=True)
    
    print("Building Silent Portable SP Crew Hub...")
    print(f"Using source: {portable_hub_dir / 'portable_hub_silent.py'}")
    
    # PyInstaller spec content for silent build
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE

project_root = r"{project_root}"
hub_dir = r"{hub_dir}"

a = Analysis(
    [os.path.join(project_root, 'portable-hub', 'portable_hub_silent.py')],
    pathex=[project_root, hub_dir],
    binaries=[
        (os.path.join(hub_dir, 'uv.exe'), '.'),
    ],
    datas=[
        (os.path.join(project_root, 'RickRoll_Small.mp4'), '.'),
    ],
    hiddenimports=[
        'supabase',
        'gotrue',
        'postgrest', 
        'realtime',
        'storage3',
        'httpx',
        'pydantic',
        'rich',
        'keyboard',
        'requests',
        'zipfile',
        'shutil',
        'asyncio',
        'uuid',
        'socket',
        'hashlib',
        'json',
        'logging',
        'platform',
        'random',
        'subprocess',
        'threading',
        'time',
        'datetime',
        'pathlib',
        'typing',
        'tempfile',
        'urllib3',
        'websockets',
        'bcrypt',
        'cryptography'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['pycparser', 'cffi', 'cryptography.hazmat.bindings._rust'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SP-Crew-Hub-Silent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Silent - no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
    uac_admin=False,
    uac_uiaccess=False,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    icon=None
)
'''
    
    spec_file = hub_dir / "SP-Crew-Hub-Silent-Portable.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print(f"Created spec file: {spec_file}")
    
    # Run PyInstaller
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=hub_dir, capture_output=True, text=True)
    
    if result.returncode == 0:
        exe_path = dist_dir / "SP-Crew-Hub-Silent.exe"
        if exe_path.exists():
            print(f"Successfully built silent executable: {exe_path}")
            print(f"File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        else:
            print("❌ Build succeeded but executable not found")
            return False
    else:
        print("❌ Build failed:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

if __name__ == "__main__":
    success = build_portable_silent()
    sys.exit(0 if success else 1)