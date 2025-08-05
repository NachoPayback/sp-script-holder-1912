#!/usr/bin/env python3
"""Test the portable hub functionality"""

import sys
from pathlib import Path

def test_hub_initialization():
    """Test hub can initialize without errors"""
    try:
        from portable_hub import HubWorker
        print("[OK] HubWorker imported successfully")
        
        # Initialize hub (this will test UV, Supabase connection, etc.)
        print("Initializing hub...")
        hub = HubWorker()
        print(f"[OK] Hub initialized successfully")
        print(f"  Machine ID: {hub.machine_id}")
        print(f"  UV executable: {hub.uv_executable}")
        print(f"  Scripts directory: {hub.scripts_dir}")
        print(f"  Available scripts: {len(hub.available_scripts)}")
        
        # List first few scripts if any
        if hub.available_scripts:
            print("  Script examples:")
            for script in hub.available_scripts[:3]:
                print(f"    - {script}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Hub initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing portable hub...")
    success = test_hub_initialization()
    
    if success:
        print("\n[OK] All tests passed! Hub is ready for PyInstaller.")
        sys.exit(0)
    else:
        print("\n[ERROR] Tests failed! Fix issues before building executable.")
        sys.exit(1)