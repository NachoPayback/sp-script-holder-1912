#!/usr/bin/env python3
"""
SP Crew Scripts Launcher
Main entry point for executing bundled scripts
"""

import sys
import argparse
import importlib
import traceback
from pathlib import Path
from registry import get_available_scripts

def main():
    parser = argparse.ArgumentParser(description="SP Crew Scripts Launcher")
    parser.add_argument("--run", type=str, help="Script name to execute")
    parser.add_argument("--list", action="store_true", help="List available scripts")
    
    args = parser.parse_args()
    
    if args.list:
        scripts = get_available_scripts()
        print("Available scripts:")
        for script in sorted(scripts):
            print(f"  - {script}")
        return 0
    
    if not args.run:
        parser.print_help()
        return 1
    
    script_name = args.run
    
    try:
        # Import and run the script
        module = importlib.import_module(f"scripts.{script_name}")
        
        # Call main() if it exists, otherwise just importing should run it
        if hasattr(module, 'main'):
            module.main()
            
        return 0
        
    except ImportError:
        print(f"Error: Script '{script_name}' not found")
        print("Use --list to see available scripts")
        return 1
        
    except Exception as e:
        print(f"Error running script '{script_name}': {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())