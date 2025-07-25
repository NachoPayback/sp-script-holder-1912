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
cd src
python hub.py
# or with UV (recommended):
uv run python src/hub.py

# Install dependencies
pip install -r build/requirements.txt
# or with UV:
uv pip install -r build/requirements.txt
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

## Development Notes

- Uses asyncio for asynchronous operations in hub
- NATS subject format: `prankhub.control.<hub_id>` and `prankhub.status.<hub_id>`
- Pairing codes are 6-character alphanumeric strings
- Scripts execute with configurable timeout (default 30s)
- Activity logging includes timestamps and script names
- Auto-discovery eliminates manual pairing process