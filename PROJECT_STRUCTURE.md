# SP Crew Hub Project Structure

## Overview
This project contains the SP Crew Hub system with bundled scripts for fast, parallel execution.

## Directory Structure

```
├── hub/                          # Hub executable source code
│   ├── sp_crew_hub.py           # Main hub application
│   ├── program_sync_bundled.py  # Downloads and manages scripts.exe
│   ├── program_sync.py          # Legacy individual exe sync (backup)
│   └── pyproject.toml           # Hub dependencies
│
├── scripts_package/             # Bundled scripts source
│   ├── launcher.py              # Scripts.exe entry point
│   ├── registry.py              # Auto-discovers available scripts
│   ├── assets_helper.py         # Centralized asset path helper
│   ├── pyproject.toml           # Scripts package dependencies
│   ├── scripts/                 # Individual script modules
│   │   ├── taco_bell_bong.py
│   │   ├── rickroll_prank.py
│   │   └── ... (all other scripts)
│   └── assets/                  # Centralized assets
│       ├── sounds/              # Audio files
│       ├── videos/              # Video files
│       └── images/              # Image files
│
├── scripts/                     # Original individual scripts (reference)
│   └── ... (organized by script type)
│
├── remote/                      # Web interface for controlling hubs
│   └── ... (React/TypeScript app)
│
├── dist/                        # Built executables
│   ├── scripts.exe              # Bundled scripts package (30MB)
│   ├── version.json             # Version tracking for scripts.exe
│   ├── SP-Crew-Hub-Silent.exe   # Silent hub (no console)
│   └── SP-Crew-Hub-Terminal.exe # Terminal hub (with logs)
│
├── build_scripts_package.py     # Builds scripts.exe
├── build_hub.py                 # Builds hub executables
├── build_and_package_all.py     # Builds everything
└── build_simple_hub.py          # Simple hub builder
```

## Key Files

### Production Executables (dist/)
- **scripts.exe** - All scripts bundled in one fast-loading package
- **SP-Crew-Hub-Terminal.exe** - Hub with clean terminal output
- **SP-Crew-Hub-Silent.exe** - Hub that runs completely hidden
- **version.json** - Version info for automatic script updates

### Build Scripts
- **build_and_package_all.py** - Main build script (builds everything)
- **build_scripts_package.py** - Builds only scripts.exe
- **build_hub.py** - Builds only hub executables

## How It Works

1. **Hub downloads scripts.exe** from GitHub automatically
2. **Hub spawns scripts instantly** using `scripts.exe --run script_name`
3. **Multiple scripts run in parallel** - true spamming capability
4. **Clean terminal output** - no JSON spam, just ►, ✓, ✗

## Adding New Scripts

1. Add your script to `scripts_package/scripts/`
2. Add any assets to `scripts_package/assets/`
3. Run `python build_scripts_package.py`
4. Commit and push `dist/scripts.exe` and `dist/version.json`
5. Hub will auto-download the update

## Performance

- **Script spawn time:** ~1-2ms after first run
- **Parallel execution:** Unlimited simultaneous scripts
- **Network delay:** 50-200ms (unavoidable remote→hub latency)
- **Package size:** 30MB total (vs 15x individual 2MB executables)