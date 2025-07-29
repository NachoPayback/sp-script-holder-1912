#!/usr/bin/env python3
"""
Plays the iconic Taco Bell bong sound - Wrapper script
"""

import os
import subprocess
import sys


def main():
    """Execute the actual Taco Bell bong script from its subfolder"""
    # Get the directory where this wrapper script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the actual script in the subfolder
    actual_script = os.path.join(script_dir, "taco_bell_bong", "taco_bell_bong.py")

    if os.path.exists(actual_script):
        # Execute the actual script as a subprocess to preserve context
        try:
            subprocess.run([sys.executable, actual_script], check=True, capture_output=True)
        except Exception:
            # Fallback if subprocess fails
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
    else:
        # Fallback if subfolder script is missing
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

if __name__ == "__main__":
    main()
