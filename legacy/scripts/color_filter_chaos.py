#!/usr/bin/env python3
"""
Randomly applies Windows color filters for 10 seconds using Magnification API
"""

import ctypes
import random
import time
from ctypes import POINTER, Structure, c_float


# Windows Magnification API structures and constants
class MAGCOLOREFFECT(Structure):
    _fields_ = [("transform", c_float * 5 * 5)]

# Load Magnification API
try:
    mag = ctypes.windll.Magnification
except Exception:
    mag = None

# Color effect matrices for different filters
IDENTITY_MATRIX = [
    1.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 1.0, 0.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 0.0, 1.0
]

GRAYSCALE_MATRIX = [
    0.299, 0.299, 0.299, 0.0, 0.0,
    0.587, 0.587, 0.587, 0.0, 0.0,
    0.114, 0.114, 0.114, 0.0, 0.0,
    0.0,   0.0,   0.0,   1.0, 0.0,
    0.0,   0.0,   0.0,   0.0, 1.0
]

INVERTED_MATRIX = [
    -1.0,  0.0,  0.0, 0.0, 0.0,
     0.0, -1.0,  0.0, 0.0, 0.0,
     0.0,  0.0, -1.0, 0.0, 0.0,
     0.0,  0.0,  0.0, 1.0, 0.0,
     1.0,  1.0,  1.0, 0.0, 1.0
]

DEUTERANOPIA_MATRIX = [
    0.625, 0.7,   0.0,   0.0, 0.0,
    0.375, 0.3,   0.3,   0.0, 0.0,
    0.0,   0.0,   0.7,   0.0, 0.0,
    0.0,   0.0,   0.0,   1.0, 0.0,
    0.0,   0.0,   0.0,   0.0, 1.0
]

PROTANOPIA_MATRIX = [
    0.567, 0.558, 0.0,   0.0, 0.0,
    0.433, 0.442, 0.242, 0.0, 0.0,
    0.0,   0.0,   0.758, 0.0, 0.0,
    0.0,   0.0,   0.0,   1.0, 0.0,
    0.0,   0.0,   0.0,   0.0, 1.0
]

TRITANOPIA_MATRIX = [
    0.95,  0.0,   0.0,   0.0, 0.0,
    0.05,  0.433, 0.475, 0.0, 0.0,
    0.0,   0.567, 0.525, 0.0, 0.0,
    0.0,   0.0,   0.0,   1.0, 0.0,
    0.0,   0.0,   0.0,   0.0, 1.0
]

def apply_color_matrix(matrix):
    """Apply a color transformation matrix using Magnification API"""
    if not mag:
        return False

    try:
        # Initialize Magnification API
        if not mag.MagInitialize():
            return False

        # Create color effect structure
        effect = MAGCOLOREFFECT()
        for i in range(5):
            for j in range(5):
                effect.transform[i][j] = matrix[i * 5 + j]

        # Apply the color effect
        result = mag.MagSetFullscreenColorEffect(POINTER(MAGCOLOREFFECT)(effect))

        return bool(result)
    except Exception as e:
        print(f"Error applying color effect: {e}")
        return False

def reset_color_effect():
    """Reset to normal colors"""
    return apply_color_matrix(IDENTITY_MATRIX)

def color_filter_chaos():
    """Apply random color filter for 10 seconds"""

    # Available filters
    filters = [
        ("Grayscale", GRAYSCALE_MATRIX),
        ("Inverted", INVERTED_MATRIX),
        ("Deuteranopia (Red-Green)", DEUTERANOPIA_MATRIX),
        ("Protanopia (Red-Green)", PROTANOPIA_MATRIX),
        ("Tritanopia (Blue-Yellow)", TRITANOPIA_MATRIX),
    ]

    # Choose random filter
    filter_name, filter_matrix = random.choice(filters)
    print(f"Applying {filter_name} filter...")

    # Apply the filter
    if apply_color_matrix(filter_matrix):
        print(f"Color filter '{filter_name}' applied!")

        # Wait 10 seconds
        time.sleep(10)

        # Restore normal colors
        print("Restoring original colors...")
        reset_color_effect()

        # Uninitialize Magnification API
        if mag:
            mag.MagUninitialize()

        print("Colors restored!")
    else:
        print("Failed to apply color filter - Magnification API may not be available")

if __name__ == "__main__":
    color_filter_chaos()
