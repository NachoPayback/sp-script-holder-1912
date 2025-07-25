# P_Buttons - Distributed Automation System

A distributed automation system with two main components:
- **Hub**: Python application that runs on target machines, manages automation scripts, and communicates via NATS
- **Remote**: Flask web application that provides remote control interface

## Architecture

```
Hub (Python) ←→ NATS Server ←→ Remote Apps (Flask)
```

- **Hub**: Runs on target machine, executes automation scripts, manages Git repo
- **Remotes**: Web-based control interface with auto-discovery (up to 6 remotes)
- **NATS**: Messaging system for communication (demo.nats.io by default)
- **Git**: Script management and updates

## Quick Start

### Hub Setup

#### Requirements
- Python 3.8+
- Git installed
- Windows 10+

#### Installation

```bash
# Install dependencies
pip install -r build/requirements.txt
# or with UV (recommended):
uv pip install -r build/requirements.txt

# Run the hub (from project root)
cd src
python hub.py
```

### Remote Setup

```bash
# Run the remote (from project root)
cd src/remote
python remote_app.py
# Open browser to http://127.0.0.1:5001
```

## Connection Process

The system uses auto-discovery - no manual pairing required:

1. **Hub Side**: Run `python src/hub.py`
2. **Remote Side**: Run `python src/remote/remote_app.py` and open http://127.0.0.1:5001
3. **Auto-Connection**: Remotes automatically discover and connect to available hubs

Both hub and remote connect to the same NATS server (demo.nats.io by default), enabling cross-network discovery.

## Directory Structure

```
P_Buttons/
├── src/                      # Source code
│   ├── hub.py               # Main hub application
│   └── remote/              # Remote application
│       ├── remote_app.py    # Flask server
│       └── templates/       # Web UI templates
├── config/                  # Configuration files
│   ├── config.json         # Hub configuration
│   ├── remote_config.json  # Remote settings
│   └── *.json              # Auto-generated config files
├── scripts/                 # Automation scripts
│   ├── *.py                # Python scripts
│   ├── *.ps1               # PowerShell scripts
│   └── *.bat               # Batch scripts
├── logs/                   # Activity logs
├── build/                  # Build scripts and requirements
└── docs/                   # Documentation
```

## Usage

### Remote Operations
- **Main Button**: Execute assigned automation command
- **Shuffle**: Request new command assignment
- **Timer**: Enable automatic shuffling
- **Script Management**: View and toggle available scripts

### Hub Operations
- **Silent Execution**: All commands run in background
- **Git Integration**: Automatic script updates
- **Random Assignment**: Each remote gets different commands
- **Logging**: All activities logged to `logs/` directory

## Script Management (Git-Only Workflow)

**All script management is handled through Git for security and version control.**

### Setup Git Repository
1. Create a dedicated repository for your automation scripts
2. Set `git_repo_url` in `config/config.json`
3. Ensure the hub machine has Git access to the repository

### Adding/Updating Scripts
1. **Add scripts** to your Git repository
   - Supported formats: `.py`, `.ps1`, `.bat`, `.exe`
   - Follow naming conventions in `scripts/SCRIPT_CONVENTIONS.md`
2. **Commit and push** changes to the repository
3. **Hub auto-detects** new scripts on next execution cycle
4. **Remotes can view/toggle** scripts through the web interface

### Benefits of Git-Only Approach
- **Version Control**: Full history of script changes
- **Security**: No file uploads through web interface
- **Collaboration**: Multiple admins can manage scripts
- **Backup**: Git repository serves as backup
- **Consistency**: All environments stay synchronized

## Configuration

### Hub Configuration (`config/config.json`)
```json
{
  "nats_url": "nats://demo.nats.io:4222",
  "subject_prefix": "automation",
  "git_repo_url": "https://github.com/yourusername/automation-scripts.git",
  "command_timeout": 30,
  "hub_capacity": 6
}
```

## Building Executables

### Remote Application
```bash
cd build
python build_remote.py
# Creates PButtons_Remote.exe in src/remote/dist/
```

## Requirements

### Hub Requirements
- Windows 10+
- Python 3.8+
- Git
- Internet connection for NATS

### Remote Requirements
- Windows/macOS/Linux
- Python 3.8+
- Internet connection

## Development

See `docs/CLAUDE.md` for detailed development instructions and architecture information.

## License

MIT License - see LICENSE file for details.