# SP Crew Hub System

A fast, parallel script execution system with remote control capabilities.

## 🏗️ Architecture

- **Hub** (`hub/`) - Downloads and executes bundled scripts via remote commands
- **Scripts Package** (`scripts_package/`) - All scripts bundled in one fast-loading executable  
- **Remote** (`remote/`) - Web interface for controlling hubs

## 🚀 Quick Start

### For Users
1. Download `SP-Crew-Hub-Terminal.exe` from releases
2. Run it - it will auto-download scripts and connect
3. Use the web remote to trigger scripts instantly

### For Developers

**Build everything:**
```bash
python build_tools/build_and_package_all.py
```

**Build just scripts:**
```bash
python build_tools/build_scripts_package.py
```

**Build just hubs:**
```bash
python build_tools/build_hub.py
```

## ⚡ Key Features

- **Fast execution** - Scripts spawn in 1-2ms (vs 2-3s individual EXEs)
- **Parallel processing** - Spam scripts simultaneously without blocking
- **Remote control** - Web interface for triggering scripts on any hub
- **Auto-updates** - Hub downloads script updates automatically
- **Clean output** - No JSON spam, just ►, ✓, ✗ indicators

## 📱 Usage

1. **Start Hub**: Run `SP-Crew-Hub-Terminal.exe`
2. **Open Remote**: Visit the web interface
3. **Execute Scripts**: Click buttons to run scripts on hubs
4. **Spam Away**: Click rapidly for parallel execution

## 🔧 Adding Scripts

1. Add script to `scripts_package/scripts/`
2. Add assets to `scripts_package/assets/`
3. Rebuild: `python build_tools/build_scripts_package.py`
4. Commit and push - hubs auto-update

## 📊 Performance Improvements

The bundled approach provides massive performance gains:

- **Old:** 15 individual EXEs, 2-3s startup each, no parallel execution
- **New:** 1 bundled EXE, 1-2ms startup, unlimited parallel execution
- **Result:** True spamming capability with instant response

## 📚 Documentation

- [Script Creation Guide](docs/SCRIPT_CREATION_GUIDE.md) - How to create new scripts
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed directory structure  
- [Database Setup](docs/database-setup.sql) - Supabase schema
- [Architecture](docs/remote_hub_architecture.md) - System design

## 🛠️ Development

- **Hub**: Python 3.10+, PyInstaller for packaging
- **Scripts**: Python with centralized asset management
- **Remote**: React/TypeScript, deployed on Vercel
- **Database**: Supabase for real-time messaging