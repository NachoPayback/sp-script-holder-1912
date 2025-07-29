#!/usr/bin/env python3
"""
Lint script for P_Buttons - runs both ruff and pyright
"""

import subprocess
import sys


def main():
    """Run linting tools"""
    print("[LINT] Running ruff...")
    result1 = subprocess.run([sys.executable, "-m", "ruff", "check", "scripts/", "src/"])
    
    print("\n[LINT] Running pyright...")
    result2 = subprocess.run([sys.executable, "-m", "pyright", "scripts/", "src/"])
    
    if result1.returncode == 0 and result2.returncode == 0:
        print("\n[SUCCESS] All checks passed!")
        return 0
    else:
        print("\n[ERROR] Some checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())