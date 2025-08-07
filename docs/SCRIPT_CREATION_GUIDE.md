# SP Crew Scripts - Creation Guide

## Overview
SP Crew uses a centralized script package system where all scripts are bundled into one `scripts.exe` file for fast loading and execution.

## Script Requirements

### 1. **File Structure**
```
scripts_package/scripts/your_script.py
```

### 2. **Basic Template**
```python
#!/usr/bin/env python3
"""
Your Script Name - Brief description of what it does
"""

def main():
    """Main entry point for the script"""
    # Your script logic here
    print("Script executed!")

if __name__ == "__main__":
    main()
```

### 3. **Required Elements**
- ✅ `main()` function as entry point
- ✅ `if __name__ == "__main__":` guard
- ✅ Docstring describing the script
- ✅ Error handling for robust execution

## Using Assets

### Asset Types Supported
- **Images**: `.png`, `.ico`, `.jpg`
- **Sounds**: `.wav`, `.mp3` 
- **Videos**: `.mp4`

### Asset Storage
```
scripts_package/assets/
├── images/
│   ├── Clippy.png
│   └── W_Logo1.ico
├── sounds/
│   ├── clippyping.wav
│   └── taco-bell-bong-sfx.mp3
└── videos/
    ├── Explosion.mp4
    └── RickRoll_Small.mp4
```

### Asset Usage in Scripts
```python
#!/usr/bin/env python3
"""
Example script using centralized assets
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets_helper import get_image, get_sound, get_video

def main():
    """Main script function"""
    try:
        # Load assets
        image_path = get_image("my_image.png")
        sound_path = get_sound("my_sound.wav") 
        video_path = get_video("my_video.mp4")
        
        # Check if assets exist
        if not image_path.exists():
            print("Image not found!")
            return
            
        # Use the assets...
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## Script Categories & Examples

### 1. **System Control Scripts**
- `lock_pc.py` - Lock the computer
- `minimize_windows.py` - Minimize all windows
- `screen_rotation_prank.py` - Rotate display

### 2. **Visual Pranks** 
- `screen_blocker.py` - Block part of screen with colored rectangle
- `explosion_overlay.py` - Fullscreen video overlay
- `change_desktop_icons.py` - Change desktop shortcut icons

### 3. **Audio Scripts**
- `play_sound.py` - Play system sounds
- `taco_bell_bong.py` - Play specific sound files

### 4. **Input Pranks**
- `move_mouse.py` - Move mouse cursor randomly
- `keyboard_scrambler.py` - Type random characters

### 5. **Fake UI Scripts**
- `fake_clippy.py` - Show fake Microsoft Clippy
- `fake_progress_bars.py` - Show fake system dialogs
- `fake_system_message.py` - Show fake Windows notifications

## Best Practices

### Code Style
- Use descriptive function names
- Include error handling with try/catch
- Print status messages for debugging
- Keep scripts focused on one task

### Example with Error Handling
```python
def main():
    """Main script function"""
    try:
        print("Starting script...")
        
        # Your logic here
        result = do_something()
        
        if result:
            print("Script completed successfully!")
        else:
            print("Script failed!")
            
    except Exception as e:
        print(f"Error during execution: {e}")
        return False
    
    return True
```

### Windows-Specific Features
```python
import ctypes
import subprocess

# Windows API calls
user32 = ctypes.windll.user32
result = user32.SomeWindowsFunction()

# PowerShell execution
ps_script = '''
# PowerShell code here
'''
subprocess.run(["powershell", "-Command", ps_script], 
               creationflags=subprocess.CREATE_NO_WINDOW)
```

## Adding New Scripts

### Step 1: Create Script File
1. Create `scripts_package/scripts/my_script.py`
2. Follow the template above
3. Test locally with Python

### Step 2: Add Assets (if needed)
1. Place assets in appropriate `scripts_package/assets/` subfolder
2. Use `assets_helper` to load them in your script

### Step 3: Update Build Config
Add your script to `build_tools/build_scripts_package.py`:
```python
hiddenimports=[
    # ... other imports ...
    'scripts.my_script',
]
```

### Step 4: Build and Deploy
1. Run `python build_tools/build_scripts_package.py`
2. Commit and push to GitHub
3. Hub automatically detects new scripts on next run

## Testing Scripts

### Local Testing
```bash
# Test individual script
python scripts_package/scripts/my_script.py

# Test via launcher
python scripts_package/launcher.py --run my_script
```

### Production Testing
1. Build scripts package
2. Test with built executable: `dist/scripts.exe --run my_script`
3. Deploy and test through hub

## Common Patterns

### Auto-closing Windows
```python
import time
import threading

def auto_close_window(window, delay=10):
    """Auto close a window after delay"""
    def close_after_delay():
        time.sleep(delay)
        try:
            window.quit()
            window.destroy()
        except:
            pass
    
    thread = threading.Thread(target=close_after_delay, daemon=True)
    thread.start()
```

### Random Selection
```python
import os

# Cryptographically secure random
def get_random_choice(options):
    random_bytes = os.urandom(1)[0]
    return options[random_bytes % len(options)]

# Usage
colors = ['red', 'blue', 'green']
selected_color = get_random_choice(colors)
```

### Cross-Platform Compatibility
```python
import sys

if sys.platform == "win32":
    # Windows-specific code
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, "Hello", "Title", 1)
else:
    print("This script requires Windows")
```

## Script Naming Convention
- Use snake_case: `my_awesome_script.py`
- Be descriptive: `rotate_screen_randomly.py` not `rotate.py`
- Avoid conflicts with Python modules

## Troubleshooting

### Common Issues
1. **Import errors**: Check `assets_helper` import path
2. **Asset not found**: Verify file exists in assets folder
3. **Script not detected**: Check it's in `scripts/` folder with `.py` extension
4. **Build fails**: Ensure script has proper `main()` function

### Debug Tips
- Test scripts individually before building
- Use print statements for debugging
- Check hub logs for execution errors
- Verify assets exist and are accessible

## Security Notes
- Scripts run with user privileges
- Be careful with system modifications
- Always include restoration/cleanup code
- Test thoroughly before deployment