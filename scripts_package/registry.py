#!/usr/bin/env python3
"""
Script Registry - Auto-discovers available scripts
"""

import os
from pathlib import Path

def get_available_scripts():
    """Get list of available script names"""
    scripts_dir = Path(__file__).parent / "scripts"
    scripts = []
    
    if scripts_dir.exists():
        for file in scripts_dir.glob("*.py"):
            if file.name != "__init__.py" and not file.name.startswith("_"):
                scripts.append(file.stem)
    
    return scripts

def get_script_manifest():
    """Get detailed manifest of all scripts with metadata"""
    scripts = get_available_scripts()
    manifest = {}
    
    for script in scripts:
        friendly_name = script.replace('_', ' ').title()
        manifest[script] = {
            "name": script,
            "friendly_name": friendly_name,
            "module": f"scripts.{script}"
        }
    
    return manifest