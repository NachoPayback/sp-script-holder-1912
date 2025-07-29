# Automation Scripts Repository

This directory contains automation scripts that can be executed by the hub when remotes press their buttons.

## Script Types Supported

- **Python scripts** (`.py`) - Executed with Python interpreter
- **PowerShell scripts** (`.ps1`) - Executed with PowerShell
- **Batch files** (`.bat`) - Executed with Windows Command Prompt
- **Executable files** (`.exe`) - Executed directly

## Current Scripts

### Python Scripts
- `play_sound.py` - Plays random Windows system sounds
- `rotate_screen.py` - Temporarily adjusts screen orientation
- `fake_system_message.py` - Displays system notification messages
- `move_mouse.py` - Randomly adjusts mouse cursor position
- `minimize_windows.py` - Temporarily minimizes all windows

### PowerShell Scripts
- `system_maintenance.ps1` - Creates system optimization and update effects

## Git Integration

The hub automatically pulls new scripts from this repository when:
1. A remote user triggers a script refresh
2. The hub receives a script update request

### Setting Up Git Repository

1. **Create a private GitHub repository** for your automation scripts
2. **Update the hub configuration** (`config.json`):
   ```json
   {
     "git_repo_url": "https://github.com/yourusername/automation-scripts.git"
   }
   ```
3. **Add your scripts** to the repository
4. **Push to GitHub** - the hub will pull them automatically

### Adding New Scripts

1. **Create your script** in any supported language
2. **Make it executable** and safe (no system damage!)
3. **Add it to the repository**
4. **Push to GitHub**
5. **Trigger script refresh** from any remote app

## Script Guidelines

### Safety Rules
- ✅ **Harmless effects only** - no system damage
- ✅ **Temporary effects** - everything should be reversible
- ✅ **Professional appearance** - scripts should appear legitimate
- ❌ **No malicious code** - keep it safe and functional
- ❌ **No permanent changes** - don't break anything

### Best Practices
- Include error handling in your scripts
- Add comments explaining what the script does
- Test scripts thoroughly before adding to repository
- Keep execution time under 30 seconds (configurable timeout)
- Return proper exit codes (0 for success, 1 for error)
- Make scripts appear like legitimate system tools

## Example Script Structure

```python
#!/usr/bin/env python3
"""
Description of what this automation script does
"""

import sys
import random

def main():
    """Main automation function"""
    try:
        # Your automation code here
        print("Process executed successfully!")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Security Notes

- Scripts are executed locally on the hub machine
- No scripts are transmitted over the network
- Git repository should be private
- Hub only pulls scripts, never pushes
- All script execution is logged locally

## Troubleshooting

- **Script not appearing?** - Check file extensions and permissions
- **Script failing?** - Check hub logs in `logs/hub.log`
- **Git pull failing?** - Verify repository URL and credentials
- **Timeout errors?** - Increase `command_timeout` in config.json