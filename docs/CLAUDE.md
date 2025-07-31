# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

P-Buttons is a distributed automation system consisting of:
- **Hub Worker** (Python): Local service that executes scripts and manages real-time communication
- **Remote Controller** (JavaScript/HTML): Web interface providing button-based script execution
- **Scripts Directory**: Collection of automation scripts (pranks, utilities, system tools)

The system uses Supabase for real-time messaging, user management, and data persistence.

## Architecture

### Core Components
- `v2/hub/hub.py` - Main hub worker service (headless Python application)
- `v2/remote-vercel/` - Web-based remote controller interface
- `scripts/` - Individual script directories with dependencies
- `v2/database/migration_steps.sql` - Database schema migrations

### Key Dependencies
- **Hub**: `supabase`, `asyncio`, `uv` (for script dependency management)
- **Scripts**: Various per-script dependencies managed via individual `pyproject.toml` files
- **Remote**: Vanilla JavaScript with Supabase client library

## Common Development Commands

### Hub Development
```bash
# Run hub worker locally
cd v2/hub
python hub.py

# Build portable executable
python build_portable_hub.py
```

### Remote Development & Deployment
```bash
# Work on remote controller
cd v2/remote-vercel

# Deploy to Vercel (REQUIRED - no remote work is complete without this)
vercel --prod

# Preview deployment
vercel

# Check deployment status
vercel ls

# View deployment logs
vercel logs
```

### Script Development
```bash
# Install script dependencies (UV will auto-install from pyproject.toml)
cd scripts/[script_name]
uv sync

# Test script execution
uv run [script_name].py
```

### Code Quality
```bash
# Run linting
ruff check

# Run type checking  
pyright

# Format code
ruff format
```

### Database Management
Database schema is managed through Supabase. **ALWAYS use MCP tools** for Supabase operations:
- Use `mcp__supabase__*` tools for all database interactions
- Apply migrations from `v2/database/migration_steps.sql` via MCP tools
- Never manually edit database schema without using MCP tools

## Script Structure

Scripts are organized in subdirectories under `scripts/`:
- Each script directory contains the main script file (`[name].py` or `[name].ps1`)
- Dependencies are managed via `pyproject.toml` in each script directory
- The hub worker uses UV to automatically install and manage script dependencies
- Scripts are executed in isolated environments with their specific dependencies

## Key Configuration

### Supabase Connection
Configuration stored in `v2/config/supabase.json`:
- Database URL and anonymous key for real-time messaging
- Used by both hub worker and remote controller

### Hub Registration
Hubs register automatically using machine-specific identifiers:
- Machine ID generated from hostname + hardware info
- Supports multiple modes: "shared" (all scripts visible) vs "assigned" (one script per remote)
- Real-time presence tracking for online/offline status

## Real-time Communication Flow

**CRITICAL**: Communication methods MUST be consistent across all three components:

1. **Hub Registration**: Hub worker registers with Supabase, updates script inventory
2. **Remote Connection**: Web remotes connect to available hubs
3. **Script Assignment**: Based on hub mode, scripts are assigned to remotes
4. **Command Execution**: Button presses create database entries, trigger real-time events
5. **Script Execution**: Hub worker receives commands, executes scripts, stores results

### Communication Consistency Requirements
- **Database Schema**: All components must use identical table structures and field names
- **Real-time Events**: Event names, payload structures, and channel subscriptions must match exactly
- **Data Types**: UUID formats, timestamp formats, and enum values must be consistent
- **API Contracts**: Any changes to database structure require updates to hub (Python) AND remote (JavaScript)
- **Testing**: Always test communication flow between all three components after changes

## Deployment

### Hub Deployment
- Use `build_portable_hub.py` to create standalone executable
- Executable includes Python runtime + all dependencies (~80-120MB)
- No Python installation required on target machines

### Remote Deployment
- **MANDATORY**: Deploy to Vercel using `vercel --prod` 
- **NO remote work is considered complete** until pushed to Vercel
- Configure Supabase environment variables in Vercel dashboard
- Web interface adapts to available hubs automatically
- Always verify deployment works with live hub connections

## Important Notes

- Scripts must be placed in individual subdirectories under `scripts/`
- Hub worker automatically discovers and installs script dependencies
- **ALWAYS use MCP Supabase tools** for any database operations or queries
- Real-time functionality requires proper Supabase configuration
- Database schema changes should be applied via migration files using MCP tools
- All script execution is logged and tracked in the database
- **Vercel deployment is mandatory** for any remote controller changes
- Communication protocols between hub/remote/database must remain synchronized