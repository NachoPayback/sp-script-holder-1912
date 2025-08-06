#!/usr/bin/env python3
"""
Assets Helper - Provides paths to bundled assets
"""

import os
import sys
from pathlib import Path

def get_asset_path(asset_type: str, filename: str) -> Path:
    """Get path to an asset file
    
    Args:
        asset_type: 'sounds', 'videos', or 'images'
        filename: Name of the asset file
        
    Returns:
        Path object to the asset
    """
    # When running as exe, assets are in _internal
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS) / "assets"
    else:
        base_path = Path(__file__).parent / "assets"
    
    return base_path / asset_type / filename

def get_sound(filename: str) -> Path:
    """Get path to a sound file"""
    return get_asset_path("sounds", filename)

def get_video(filename: str) -> Path:
    """Get path to a video file"""
    return get_asset_path("videos", filename)

def get_image(filename: str) -> Path:
    """Get path to an image file"""
    return get_asset_path("images", filename)