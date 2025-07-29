# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

P_Buttons is a distributed automation system with two main components:
- **Hub**: Python application that runs on target machines, manages automation scripts, and communicates via NATS
- **Remote**: Flask web application that provides remote control interface

## Common Commands

### Hub Application
```bash
# Run the hub (from project root)
uv run python src/hub.py

# Install dependencies (ALWAYS use UV, not pip)
uv sync  # Installs all dependencies from pyproject.toml
uv add <package-name>  # Add new dependency to pyproject.toml
```

### Remote Application
```bash
# Run the remote (from project root)
cd src/remote
python remote_app.py  # Runs on http://127.0.0.1:5001
```

### Testing
```bash
# Run tests (when available)
pytest
```

## Architecture

### Communication Flow
1. Hub connects to NATS server and subscribes to control subjects
2. Remote app connects to NATS and publishes commands
3. Hub executes scripts locally based on received commands
4. Pairing uses temporary codes displayed via Ctrl+Alt+S+P hotkey

### Key Components

**Hub (`src/hub.py`)**:
- Manages script execution and NATS messaging
- Auto-connects remotes without pairing codes
- Stores pairing info in `config/paired_remotes.json`
- Logs activity to `logs/hub_*.log`

**Remote (`src/remote/remote_app.py`)**:
- Flask server with web UI for remote control
- Auto-discovers and connects to available hubs
- Communicates with hub via NATS messaging

**Configuration (`config/config.json`)**:
- NATS connection settings
- Git repository URL for scripts
- Hotkey configuration
- Timeout and hub capacity settings

### Script Management
- **Git-Only Workflow**: All scripts managed through Git repository
- Scripts stored in `scripts/` directory
- Supports Python (.py), PowerShell (.ps1), Batch (.bat), and Executables (.exe)
- Hub automatically syncs from configured `git_repo_url`
- No script upload through web interface (removed for security)
- Remotes can view and toggle scripts only
- **Centralized Dependencies**: All script dependencies managed in main `pyproject.toml`

## Development Notes

- Uses asyncio for asynchronous operations in hub
- NATS subject format: `prankhub.control.<hub_id>` and `prankhub.status.<hub_id>`
- Pairing codes are 6-character alphanumeric strings
- Scripts execute with configurable timeout (default 30s)
- Activity logging includes timestamps and script names
- Auto-discovery eliminates manual pairing process

## UV Embedding System (2025)

**Zero-Installation Deployment:**
- Hub automatically downloads UV binary on first run
- UV installs Python + dependencies from `pyproject.toml`
- Python scripts run via embedded UV environment
- Works on clean VMs with no Python installed

**Deployment Process:**
1. Deploy hub.exe to target machine
2. Hub downloads UV (~15MB) automatically
3. UV installs Python environment (~50MB total)  
4. Scripts run with all dependencies available

**Directory Structure After Setup:**
```
P_Buttons/
├── hub.exe                # Main hub executable
├── uv_embedded/           # Auto-created
│   └── uv.exe            # Downloaded UV binary
├── .venv/                # Auto-created by UV
│   └── ...               # Python + dependencies
└── scripts/              # Your prank scripts (.py files)
```

## Recent Script Additions

**New Prank Scripts (2025-01-28):**
- `browser_tab_chaos.py` - Opens multiple browser tabs using Selenium
- `screen_rotation_prank.py` - Rotates screen temporarily (with --reset flag)
- `cursor_size_prank.py` - Changes cursor size temporarily (with --reset flag)  
- `youtube_wallpaper_prank.py` - Sets random YouTube thumbnail as wallpaper

**Reset Functionality:**
```bash
# Emergency resets if scripts crash mid-execution
python screen_rotation_prank.py --reset
python cursor_size_prank.py --reset
```

**Additional Dependencies:**
- selenium>=4.0.0 (browser automation)
- rotate-screen>=1.0.0 (display rotation)
- Pillow>=9.0.0 (image processing)
- requests>=2.25.0 (HTTP requests)