#!/usr/bin/env python3
"""
Test script for P_Buttons - validates all components work
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def test_script_execution():
    """Test that individual scripts can run"""
    print("[TEST] Testing individual script execution...")
    
    scripts_dir = Path("scripts")
    test_scripts = [
        ("screen_rotation_prank.py", ["--reset"]),
        ("cursor_size_prank.py", ["--reset"]),
    ]
    
    for script_name, args in test_scripts:
        script_path = scripts_dir / script_name
        if script_path.exists():
            print(f"  Testing {script_name}...")
            result = subprocess.run([sys.executable, str(script_path)] + args, 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"  [PASS] {script_name} works")
            else:
                print(f"  [FAIL] {script_name} failed: {result.stderr}")
                return False
        else:
            print(f"  [WARN] {script_name} not found")
    
    return True


def test_hub_startup():
    """Test hub can start without errors"""
    print("[TEST] Testing hub startup...")
    
    try:
        process = subprocess.Popen([sys.executable, "src/hub.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        
        # Let it run for 3 seconds
        time.sleep(3)
        process.terminate()
        
        stdout, stderr = process.communicate(timeout=5)
        
        # Check both stdout and stderr for success indicators
        output = stdout + stderr
        if "Hub" in output and "running with" in output:
            print("  [PASS] Hub starts successfully")
            return True
        else:
            print(f"  [FAIL] Hub startup issues - no success message found")
            return False
            
    except Exception as e:
        print(f"  [FAIL] Hub test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("P_Buttons System Test\n")
    
    tests = [
        ("Script Execution", test_script_execution),
        ("Hub Startup", test_hub_startup),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{test_name.upper()}]")
        if test_func():
            passed += 1
        
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All systems operational!")
        return 0
    else:
        print("[ERROR] Some systems need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())