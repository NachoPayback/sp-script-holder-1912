#!/usr/bin/env python3
"""
Lock PC - Locks the Windows PC instantly (same as Windows+L)
"""

import ctypes


def lock_computer():
    """Lock the Windows computer using Windows API"""
    try:
        # Use Windows API to lock the workstation
        # This is the same as pressing Windows+L
        result = ctypes.windll.user32.LockWorkStation()
        
        if result:
            print("Computer locked successfully!")
            return True
        else:
            print("Failed to lock computer")
            return False
            
    except Exception as e:
        print(f"Error locking computer: {e}")
        return False


def main():
    """Main entry point for the script"""
    print("Locking PC...")
    lock_computer()


if __name__ == "__main__":
    main()