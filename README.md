# SP Crew Control

Distributed automation system for remote script execution with real-time communication.

## 🏗️ Architecture

- **Hub** (`hub/`) - Python service that discovers and executes scripts
- **Remote** (`remote/`) - Web interface for controlling hubs  
- **Scripts** (`scripts/`) - Individual automation scripts with dependencies

## 🚀 Quick Start

### Build Portable Hub
```bash
cd hub
python build.py
```

### Deploy Remote Controller
```bash
cd remote  
vercel --prod
```

### Add New Scripts
1. Create directory in `hub/scripts/[script_name]/`
2. Add `[script_name].py` or `[script_name].ps1`
3. Add `pyproject.toml` for dependencies
4. Hub auto-discovers on next restart

## 📚 Documentation

- [CLAUDE.md](docs/CLAUDE.md) - Development guide for Claude Code
- [Database Setup](docs/database-setup.sql) - Supabase schema
- [Architecture](docs/remote_hub_architecture.md) - System design

## 🛠️ Development

- **Hub**: Python 3.10+, UV for dependency management
- **Remote**: Vanilla JavaScript, deployed on Vercel
- **Database**: Supabase for real-time messaging and storage