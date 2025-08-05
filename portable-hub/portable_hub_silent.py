#!/usr/bin/env python3
"""
SP Crew Control V2 - Hub Worker Service (Headless)
Pure script execution engine using Supabase real-time messaging
No web UI - just executes scripts when commanded
"""

import asyncio
import hashlib
import json
import logging
import os
import platform
import random
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Emergency shutdown hotkey support
try:
    import keyboard
    HOTKEY_AVAILABLE = True
except ImportError:
    HOTKEY_AVAILABLE = False

from supabase import Client, create_client
from supabase._async.client import create_client as create_async_client
import shutil

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

# Configuration for standalone hub with embedded scripts
# Scripts are packaged directly in the executable
WORKING_DIR = Path.home() / "SP-Crew-Hub-Scripts"

# Cache directory for downloaded scripts to avoid re-downloading
CACHE_DIR = Path.home() / "SP-Crew-Hub-Cache"

# Add project root to path for script imports
project_root = WORKING_DIR
sys.path.insert(0, str(project_root))

class HubWorker:
    def __init__(self):
        self.setup_logging()
        
        # Initialize UV executable
        self.uv_executable = None
        self.ensure_uv_installed()
        
        # Ensure working directory exists
        self.setup_working_directory()

        # Hub configuration
        self.machine_id = self.get_machine_id()
        self.hub_id = None  # Will be set after registration
        self.friendly_name = f"Hub-{socket.gethostname()}"

        # Hardcoded Supabase configuration (for executable)
        self.supabase_url = "https://qcefzjjxnwccjivsbtgb.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.async_supabase = None  # Single async client for all real-time operations
        self._async_client_lock = None  # Will be created in async context

        # Script management
        self.script_dependencies_ready = {}  # Track dependency status per script
        self.available_scripts = self.discover_scripts()

        # Real-time messaging
        self.channel = None
        self.presence_channel = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10

        # Status tracking
        self.running = True
        self.shutdown_requested = False
        
        # Command tracking to prevent duplicates
        self.processed_commands = set()
        
        # Emergency shutdown hotkey (Ctrl+Shift+Q)
        self.emergency_hotkey = "ctrl+shift+q"
        self.setup_emergency_shutdown()

        # Rich startup banner
        hotkey_text = f"[red]Emergency Shutdown:[/red] [yellow]{self.emergency_hotkey.upper()}[/yellow]" if HOTKEY_AVAILABLE else "[dim]Emergency Shutdown: Not Available[/dim]"
        startup_panel = Panel.fit(
            f"[bold blue]SP CREW CONTROL V2 - HUB WORKER[/bold blue]\n"
            f"[dim]Pure script execution engine using Supabase real-time messaging[/dim]\n\n"
            f"[green]Machine ID:[/green] [cyan]{self.machine_id}[/cyan]\n"
            f"[green]Scripts Found:[/green] [yellow]{len(self.available_scripts)}[/yellow]\n"
            f"[green]Dependencies Ready:[/green] [yellow]{sum(1 for ready in self.script_dependencies_ready.values() if ready)}[/yellow]\n"
            f"{hotkey_text}",
            title="[bold green]INITIALIZATION COMPLETE[/bold green]",
            border_style="green"
        )
        if platform.system() != "Windows":  # Only show rich panels on non-Windows
            self.console.print(startup_panel)

    def setup_logging(self):
        """Setup logging with Rich console"""
        # Create console for Rich output
        self.console = Console()
        
        # Setup logging - Windows-friendly format to avoid Unicode issues
        if platform.system() == "Windows":
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] %(levelname)s %(message)s",
                datefmt="%d/%m/%y %H:%M:%S",
                handlers=[
                    RichHandler(console=self.console, rich_tracebacks=True, markup=False),
                    logging.FileHandler("hub.log", encoding='utf-8')
                ]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] %(levelname)s %(message)s",
                datefmt="%d/%m/%y %H:%M:%S",
                handlers=[
                    RichHandler(console=self.console, rich_tracebacks=True),
                    logging.FileHandler("hub.log")
                ]
            )
        self.logger = logging.getLogger(__name__)

    def setup_emergency_shutdown(self):
        """Setup emergency shutdown hotkey"""
        if not HOTKEY_AVAILABLE:
            self.logger.warning("Keyboard module not available - emergency shutdown disabled")
            return
            
        def emergency_shutdown():
            self.logger.warning("EMERGENCY SHUTDOWN TRIGGERED via Ctrl+Shift+Q")
            self.console.print("\n[bold red]EMERGENCY SHUTDOWN ACTIVATED[/bold red]")
            self.console.print("[yellow]Shutting down SP Crew Hub immediately...[/yellow]")
            self.running = False
            self.shutdown_requested = True
            # Force exit after 2 seconds if graceful shutdown fails
            threading.Timer(2.0, lambda: os._exit(0)).start()
        
        if HOTKEY_AVAILABLE:
            try:
                keyboard.add_hotkey(self.emergency_hotkey, emergency_shutdown)
                self.logger.info(f"Emergency shutdown hotkey registered: {self.emergency_hotkey.upper()}")
            except Exception as e:
                self.logger.warning(f"Could not register emergency hotkey: {e}")
        else:
            self.logger.warning("Keyboard module not available - emergency hotkey disabled")

    def fix_script_asset_paths(self, script_dir: Path):
        """Fix asset paths in scripts to work with the hub's directory structure"""
        script_name = script_dir.name
        script_file = script_dir / f"{script_name}.py"
        
        if not script_file.exists():
            return
        
        try:
            # Read the script content
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix common asset path issues
            original_content = content
            
            # Fix Clippy.png path (3 directories up -> same directory)
            content = content.replace(
                "os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Clippy.png')",
                "os.path.join(os.path.dirname(__file__), 'Clippy.png')"
            )
            
            # Fix other common asset paths
            content = content.replace(
                "os.path.join(os.path.dirname(os.path.dirname(__file__)),",
                "os.path.join(os.path.dirname(__file__),"
            )
            
            # Only write if content changed
            if content != original_content:
                with open(script_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.debug(f"Fixed asset paths in {script_name}")
                
        except Exception as e:
            self.logger.warning(f"Could not fix asset paths in {script_name}: {e}")

    def find_script_assets(self, script_dir: Path, asset_name: str) -> Optional[Path]:
        """Find script assets using multiple search strategies"""
        script_name = script_dir.name
        
        # Strategy 1: Look in the script's own directory first
        asset_path = script_dir / asset_name
        if asset_path.exists():
            return asset_path
        
        # Strategy 2: Look in parent directories (common patterns)
        for parent_level in range(1, 4):
            parent_dir = script_dir
            for _ in range(parent_level):
                parent_dir = parent_dir.parent
            asset_path = parent_dir / asset_name
            if asset_path.exists():
                return asset_path
        
        # Strategy 3: Look in the hub's assets directory
        hub_assets_dir = Path.home() / "SP-Crew-Hub-Scripts" / "assets"
        asset_path = hub_assets_dir / asset_name
        if asset_path.exists():
            return asset_path
        
        # Strategy 4: Look in the current working directory
        asset_path = Path.cwd() / asset_name
        if asset_path.exists():
            return asset_path
        
        # Strategy 5: Look in the hub's root directory
        hub_root = Path.home() / "SP-Crew-Hub-Scripts"
        asset_path = hub_root / asset_name
        if asset_path.exists():
            return asset_path
        
        self.logger.warning(f"Could not find asset '{asset_name}' for script '{script_name}'")
        return None

    def create_asset_helper_script(self, script_dir: Path):
        """Create a helper script that can find assets dynamically"""
        script_name = script_dir.name
        helper_file = script_dir / "_asset_helper.py"  # Use underscore to avoid setuptools conflicts
        
        helper_content = f'''#!/usr/bin/env python3
"""
Asset Helper for {script_name}
Dynamically finds assets using multiple search strategies
"""

import os
from pathlib import Path

def find_asset(asset_name: str, script_dir: Path = None) -> str:
    """Find an asset using multiple search strategies"""
    if script_dir is None:
        script_dir = Path(__file__).parent
    
    # Strategy 1: Look in the script's own directory first
    asset_path = script_dir / asset_name
    if asset_path.exists():
        return str(asset_path)
    
    # Strategy 2: Look in parent directories (common patterns)
    for parent_level in range(1, 4):
        parent_dir = script_dir
        for _ in range(parent_level):
            parent_dir = parent_dir.parent
        asset_path = parent_dir / asset_name
        if asset_path.exists():
            return str(asset_path)
    
    # Strategy 3: Look in the hub's assets directory
    hub_assets_dir = Path.home() / "SP-Crew-Hub-Scripts" / "assets"
    asset_path = hub_assets_dir / asset_name
    if asset_path.exists():
        return str(asset_path)
    
    # Strategy 4: Look in the current working directory
    asset_path = Path.cwd() / asset_name
    if asset_path.exists():
        return str(asset_path)
    
    # Strategy 5: Look in the hub's root directory
    hub_root = Path.home() / "SP-Crew-Hub-Scripts"
    asset_path = hub_root / asset_name
    if asset_path.exists():
        return str(asset_path)
    
    # Fallback: return the expected path in script directory
    return str(script_dir / asset_name)

def get_asset_path(asset_name: str) -> str:
    """Get the path to an asset, creating directories if needed"""
    script_dir = Path(__file__).parent
    return find_asset(asset_name, script_dir)
'''
        
        try:
            with open(helper_file, 'w', encoding='utf-8') as f:
                f.write(helper_content)
            self.logger.debug(f"Created asset helper for {script_name}")
        except Exception as e:
            self.logger.warning(f"Could not create asset helper for {script_name}: {e}")

    def setup_centralized_assets(self, scripts_dir: Path):
        """Create a centralized assets directory and copy common assets there"""
        try:
            # Create centralized assets directory
            assets_dir = Path.home() / "SP-Crew-Hub-Scripts" / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            # Find and copy common assets from scripts
            common_assets = [
                "Clippy.png", "clippyping.wav", "explosion_audio.mp3",
                "taco-bell-bong-sfx.mp3", "W_Logo1.png", "Untitled-2.png"
            ]
            
            copied_count = 0
            for script_dir in scripts_dir.iterdir():
                if script_dir.is_dir():
                    for asset_name in common_assets:
                        asset_path = script_dir / asset_name
                        if asset_path.exists():
                            dest_path = assets_dir / asset_name
                            if not dest_path.exists():
                                shutil.copy2(asset_path, dest_path)
                                copied_count += 1
                                self.logger.debug(f"Copied {asset_name} to centralized assets")
            
            if copied_count > 0:
                self.logger.info(f"Set up centralized assets directory with {copied_count} files")
                
        except Exception as e:
            self.logger.warning(f"Could not set up centralized assets: {e}")

    def install_script_dependencies(self, script_dir: Path) -> bool:
        """Install dependencies for a script using UV from pyproject.toml or inline script deps"""
        script_name = script_dir.name
        pyproject_path = script_dir / "pyproject.toml"
        script_py_path = script_dir / f"{script_name}.py"
        
        # Check if already processed
        if script_name in self.script_dependencies_ready:
            return self.script_dependencies_ready[script_name]
        
        # Check for inline script dependencies (PEP 723)
        has_inline_deps = False
        if script_py_path.exists():
            try:
                with open(script_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '# /// script' in content and 'dependencies' in content:
                        has_inline_deps = True
            except Exception:
                pass
        
        if not pyproject_path.exists() and not has_inline_deps:
            # No dependencies file or inline deps, mark as ready
            self.script_dependencies_ready[script_name] = True
            return True
            
        try:
            # Check if UV is available
            if self.uv_executable is None:
                self.logger.warning(f"[DEPS] UV not available - skipping dependencies for {script_name}")
                self.script_dependencies_ready[script_name] = False
                return False
            
            # Check if virtual environment and dependencies already exist
            venv_path = script_dir / ".venv"
            if pyproject_path.exists() and venv_path.exists():
                # Quick check if dependencies are likely installed
                site_packages = venv_path / "Lib" / "site-packages"  # Windows path
                if not site_packages.exists():
                    site_packages = venv_path / "lib" / "python"  # Unix-like fallback
                
                if site_packages.exists() and any(site_packages.iterdir()):
                    self.logger.info(f"[bright_green]Dependencies already installed[/bright_green] [bold]for[/bold] [cyan]{script_name}[/cyan]", extra={"markup": True})
                    self.script_dependencies_ready[script_name] = True
                    return True
            
            self.logger.info(f"[yellow]Installing dependencies[/yellow] [bold]for[/bold] [cyan]{script_name}[/cyan]...", extra={"markup": True})
            
            if pyproject_path.exists():
                # Initialize UV project if needed and install dependencies
                # First, create venv if it doesn't exist
                subprocess.run(
                    [self.uv_executable, "venv"],
                    cwd=script_dir,
                    capture_output=True,
                    timeout=30
                )
                
                # Install dependencies from pyproject.toml
                result = subprocess.run(
                    [self.uv_executable, "pip", "install", "-e", "."],
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                # Use inline script dependencies (PEP 723) 
                result = subprocess.run(
                    [self.uv_executable, "run", script_py_path.name, "--help"],  # This will install deps
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            
            if result.returncode == 0:
                self.logger.info(f"[bright_green]Dependencies ready[/bright_green] [bold]for[/bold] [cyan]{script_name}[/cyan]", extra={"markup": True})
                self.script_dependencies_ready[script_name] = True
                return True
            else:
                self.logger.error(f"[bright_red]Failed to install dependencies[/bright_red] [bold]for[/bold] [cyan]{script_name}[/cyan]:", extra={"markup": True})
                self.logger.error(f"[DEPS]   {result.stderr.strip()}")
                self.script_dependencies_ready[script_name] = False
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"[DEPS] Timeout installing dependencies for {script_name}")
            self.script_dependencies_ready[script_name] = False
            return False
        except Exception as e:
            self.logger.error(f"[DEPS] Error installing dependencies for {script_name}: {e}")
            self.script_dependencies_ready[script_name] = False
            return False

    def setup_working_directory(self):
        """Setup working directory with embedded scripts"""
        try:
            # Ensure working directory exists and is accessible
            WORKING_DIR.mkdir(parents=True, exist_ok=True)
            
            # Set up embedded scripts (no UV needed)
            self.setup_embedded_scripts()
            
            # Verify the scripts directory exists and has content
            scripts_dir = WORKING_DIR / "scripts"
            if not scripts_dir.exists():
                self.logger.error(f"Scripts directory not found: {scripts_dir}")
                raise FileNotFoundError(f"Scripts directory not found: {scripts_dir}")
            
            script_count = len([f for f in scripts_dir.iterdir() if f.is_dir()])
            self.logger.info(f"Using project directory: {WORKING_DIR} (found {script_count} scripts)")
            
            # Set the scripts directory path for later use
            self.scripts_dir = scripts_dir
                
        except Exception as e:
            self.logger.error(f"Error setting up working directory: {e}")
            raise

    def get_machine_id(self) -> str:
        """Generate a unique machine ID based on hardware"""
        try:
            # Get hostname
            hostname = socket.gethostname()
            
            # Try to get MAC address
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            
            # Create hash from hostname + MAC
            machine_string = f"{hostname}-{mac}"
            return hashlib.md5(machine_string.encode()).hexdigest()[:16]
        except Exception:
            # Fallback to hostname + random if MAC fails
            fallback_string = f"{socket.gethostname()}-{random.randint(1000, 9999)}"
            return hashlib.md5(fallback_string.encode()).hexdigest()[:16]

    def ensure_uv_installed(self):
        """Ensure bundled uv is available"""
        try:
            # Get path to bundled uv.exe
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable - uv.exe is in the bundle root
                bundle_dir = Path(sys._MEIPASS)
                uv_path = bundle_dir / "uv.exe"
            else:
                # Running as script
                uv_path = Path(__file__).parent / "uv.exe"
            
            if uv_path.exists():
                # Test the bundled UV
                result = subprocess.run([str(uv_path), "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.logger.info(f"Found bundled UV: {result.stdout.strip()}")
                    # Store the UV path for later use
                    self.uv_executable = str(uv_path)
                    return
            
            # Fallback: try system UV
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"Using system UV: {result.stdout.strip()}")
                self.uv_executable = "uv"
                return
                
            # If no UV found, set to None (scripts will run without dependencies)
            self.uv_executable = None
            self.logger.warning("UV not found - scripts may run without dependencies")
                
        except Exception as e:
            self.logger.error(f"Failed to find uv executable: {e}")
            self.uv_executable = None
            self.logger.warning("UV setup failed - scripts may run without dependencies")

    def check_if_scripts_need_update(self, cache_file: Path) -> bool:
        """Check if GitHub scripts are different from cached ones"""
        try:
            import requests
            import hashlib
            
            # Get GitHub repository info to check for changes
            repo_url = "https://api.github.com/repos/NachoPayback/sp-script-holder-1912/commits/master"
            
            self.logger.debug("Checking GitHub for script changes...")
            response = requests.get(repo_url, timeout=10)
            response.raise_for_status()
            
            github_data = response.json()
            latest_commit_sha = github_data.get('sha', '')
            
            # Check cached commit SHA
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    cached_sha = cache_data.get('commit_sha', '')
                    
                    if cached_sha == latest_commit_sha:
                        self.logger.debug(f"Scripts up to date (commit: {latest_commit_sha[:8]})")
                        return False  # No update needed
                    else:
                        self.logger.debug(f"Scripts outdated (cached: {cached_sha[:8]}, latest: {latest_commit_sha[:8]})")
                        return True  # Update needed
                        
                except Exception as e:
                    self.logger.warning(f"Cache file corrupted: {e}")
                    return True  # Update needed
            else:
                self.logger.debug("No cache file found")
                return True  # Update needed
                
        except Exception as e:
            self.logger.warning(f"Could not check GitHub for updates: {e}")
            # If we can't check GitHub, update only if no local scripts exist
            scripts_dest = Path.home() / "SP-Crew-Hub-Scripts" / "scripts"
            return not (scripts_dest.exists() and any(scripts_dest.iterdir()))

    def setup_embedded_scripts(self):
        """Download scripts from GitHub repository with content-based caching"""
        try:
            self.logger.debug("Checking scripts from GitHub...")
            
            # Create working directory
            project_root.mkdir(parents=True, exist_ok=True)
            scripts_dest = project_root / "scripts"
            
            # Check if current scripts match GitHub content
            cache_file = CACHE_DIR / "scripts_cache.json"
            need_update = self.check_if_scripts_need_update(cache_file)
            
            if not need_update and scripts_dest.exists() and any(scripts_dest.iterdir()):
                self.logger.info("Scripts are up to date with GitHub")
                return  # Use existing scripts
            
            self.logger.info("Scripts need updating - syncing with GitHub")
            
            # Perform incremental sync instead of full download
            self.sync_scripts_incrementally(scripts_dest)
            
            # Verify scripts were downloaded successfully
            if scripts_dest.exists() and any(scripts_dest.iterdir()):
                # Create centralized assets directory
                self.setup_centralized_assets(scripts_dest)
                
                # Cache the download info with commit SHA
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                try:
                    # Get latest commit SHA to cache
                    import requests
                    repo_url = "https://api.github.com/repos/NachoPayback/sp-script-holder-1912/commits/master"
                    response = requests.get(repo_url, timeout=10)
                    latest_commit_sha = response.json().get('sha', '') if response.status_code == 200 else ''
                    
                    with open(cache_file, 'w') as f:
                        json.dump({
                            'timestamp': datetime.now().isoformat(),
                            'commit_sha': latest_commit_sha
                        }, f)
                except Exception as e:
                    # Fallback to timestamp only
                    with open(cache_file, 'w') as f:
                        json.dump({'timestamp': datetime.now().isoformat()}, f)
                
                self.logger.info("Successfully downloaded scripts from GitHub")
            else:
                self.logger.error("Failed to download scripts - directory is empty")
                
        except Exception as e:
            self.logger.error(f"Error setting up scripts from GitHub: {e}")

    def sync_scripts_incrementally(self, scripts_dest: Path):
        """Sync scripts incrementally - only ADD/UPDATE/DELETE what changed"""
        try:
            import requests
            import zipfile
            import tempfile
            import hashlib
            
            # GitHub repository details
            repo_url = "https://github.com/NachoPayback/sp-script-holder-1912"
            scripts_url = f"{repo_url}/archive/refs/heads/master.zip"
            
            self.logger.info(f"Syncing scripts incrementally from {repo_url}")
            
            # Download the repository as ZIP to temp location
            response = requests.get(scripts_url, timeout=30)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(response.content)
                zip_path = tmp_file.name
            
            # Extract to temporary location
            temp_extract_dir = Path(tempfile.mkdtemp())
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # Find the extracted scripts directory
            github_scripts_dir = None
            for item in temp_extract_dir.iterdir():
                if item.is_dir() and (item / "scripts").exists():
                    github_scripts_dir = item / "scripts"
                    break
            
            if not github_scripts_dir:
                raise Exception("Scripts directory not found in GitHub download")
            
            # Ensure local scripts directory exists
            scripts_dest.mkdir(parents=True, exist_ok=True)
            
            # Get current local scripts
            local_scripts = set()
            if scripts_dest.exists():
                local_scripts = {item.name for item in scripts_dest.iterdir() if item.is_dir()}
            
            # Get GitHub scripts
            github_scripts = {item.name for item in github_scripts_dir.iterdir() if item.is_dir()}
            
            # Calculate changes
            to_add = github_scripts - local_scripts
            to_delete = local_scripts - github_scripts
            to_check_update = github_scripts & local_scripts
            
            changes_made = 0
            
            # DELETE removed scripts
            for script_name in to_delete:
                script_path = scripts_dest / script_name
                if script_path.exists():
                    shutil.rmtree(script_path)
                    self.logger.info(f"DELETED script: {script_name}")
                    changes_made += 1
            
            # ADD new scripts
            for script_name in to_add:
                src_path = github_scripts_dir / script_name
                dst_path = scripts_dest / script_name
                shutil.copytree(src_path, dst_path)
                self.logger.info(f"ADDED script: {script_name}")
                changes_made += 1
            
            # UPDATE changed scripts
            for script_name in to_check_update:
                src_path = github_scripts_dir / script_name
                dst_path = scripts_dest / script_name
                
                # Compare script content to see if update needed
                if self.script_content_changed(src_path, dst_path):
                    shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    self.logger.info(f"UPDATED script: {script_name}")
                    changes_made += 1
            
            # Clean up
            os.unlink(zip_path)
            shutil.rmtree(temp_extract_dir)
            
            self.logger.info(f"Script sync complete: {changes_made} changes made")
            
        except Exception as e:
            self.logger.error(f"Failed to sync scripts incrementally: {e}")
            # Fallback to full download
            self.download_scripts_from_github(scripts_dest)

    def script_content_changed(self, src_dir: Path, dst_dir: Path) -> bool:
        """Check if script directory content has changed"""
        try:
            import hashlib
            
            def get_dir_hash(directory: Path) -> str:
                """Get hash of all files in directory"""
                hash_md5 = hashlib.md5()
                
                if not directory.exists():
                    return ""
                
                # Sort files for consistent hashing
                files = sorted(directory.rglob('*'))
                for file_path in files:
                    if file_path.is_file():
                        # Include relative path and content
                        rel_path = file_path.relative_to(directory)
                        hash_md5.update(str(rel_path).encode())
                        
                        try:
                            with open(file_path, 'rb') as f:
                                hash_md5.update(f.read())
                        except Exception:
                            # Skip files we can't read
                            continue
                
                return hash_md5.hexdigest()
            
            src_hash = get_dir_hash(src_dir)
            dst_hash = get_dir_hash(dst_dir)
            
            return src_hash != dst_hash
            
        except Exception as e:
            self.logger.warning(f"Could not compare script content for {src_dir.name}: {e}")
            return True  # Assume changed if we can't compare

    def download_scripts_from_github(self, scripts_dest: Path):
        """Download scripts from GitHub repository"""
        import requests
        import zipfile
        import tempfile
        
        # GitHub repository details
        repo_url = "https://github.com/NachoPayback/sp-script-holder-1912"
        scripts_url = f"{repo_url}/archive/refs/heads/master.zip"
        
        self.logger.info(f"Downloading scripts from {repo_url}")
        
        try:
            # Download the repository as ZIP
            response = requests.get(scripts_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(response.content)
                zip_path = tmp_file.name
            
            # Extract scripts folder from ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the scripts directory in the ZIP
                scripts_in_zip = [f for f in zip_ref.namelist() if f.endswith('/scripts/') or 'scripts/' in f]
                
                if scripts_in_zip:
                    # Extract the scripts directory
                    zip_ref.extractall(project_root)
                    
                    # Find the extracted scripts directory
                    extracted_dir = None
                    for item in project_root.iterdir():
                        if item.is_dir() and (item / "scripts").exists():
                            extracted_dir = item
                            break
                    
                    if extracted_dir:
                        # Move scripts to the correct location
                        extracted_scripts = extracted_dir / "scripts"
                        if extracted_scripts.exists():
                            shutil.move(str(extracted_scripts), str(scripts_dest))
                            # Clean up the extracted directory
                            shutil.rmtree(extracted_dir)
                        else:
                            raise Exception("Scripts directory not found in downloaded ZIP")
                    else:
                        raise Exception("Could not find scripts directory in extracted files")
                else:
                    raise Exception("No scripts directory found in repository ZIP")
            
            # Clean up temporary file
            os.unlink(zip_path)
            
            self.logger.info(f"Successfully downloaded {len(list(scripts_dest.iterdir()))} scripts from GitHub")
            
        except Exception as e:
            self.logger.error(f"Failed to download scripts from GitHub: {e}")
            # Fallback: create empty scripts directory
            scripts_dest.mkdir(parents=True, exist_ok=True)
            self.logger.warning("Created empty scripts directory as fallback")



    def get_friendly_name(self, script_name: str) -> str:
        """Convert script folder name to friendly display name systematically"""
        # Systematic conversion: replace underscores with spaces and title case
        return script_name.replace('_', ' ').title()

    def discover_scripts(self) -> List[str]:
        """Scan scripts directory for available scripts in subdirectories"""
        scripts = []
        failed_deps = []

        if not self.scripts_dir.exists():
            self.logger.warning(f"Scripts directory not found: {self.scripts_dir}")
            return scripts

        self.logger.info("[DISCOVERY] Scanning for scripts and checking dependencies...")

        # Look for subdirectories containing a .py or .ps1 file with the same name
        for item in os.listdir(self.scripts_dir):
            script_path = self.scripts_dir / item
            if script_path.is_dir():
                # Check for script file with matching name
                if (script_path / f"{item}.py").exists() or (script_path / f"{item}.ps1").exists():
                    # Always add script to available list
                    scripts.append(item)
                    
                    # Fix asset paths in the script
                    self.fix_script_asset_paths(script_path)
                    
                    # Create asset helper for dynamic asset finding
                    self.create_asset_helper_script(script_path)
                    
                    # Install dependencies for this script if it has pyproject.toml
                    deps_ready = self.install_script_dependencies(script_path)
                    if not deps_ready:
                        failed_deps.append(item)

        # Report summary
        if failed_deps:
            self.logger.warning(f"[DISCOVERY] Scripts with dependency issues: {', '.join(failed_deps)}")
            self.logger.warning(f"[DISCOVERY] These scripts may fail at runtime!")
        
        ready_count = sum(1 for ready in self.script_dependencies_ready.values() if ready)
        self.logger.info(f"[bright_yellow]Script Discovery Complete[/bright_yellow] - Found [yellow]{len(scripts)}[/yellow] scripts, [green]{ready_count}[/green] with dependencies ready", extra={"markup": True})

        return scripts

    def register_hub(self):
        """Register hub using Supabase Presence"""
        try:
            # Store basic hub info in database (with status)
            hub_data = {
                "machine_id": self.machine_id,
                "friendly_name": self.friendly_name,
                "mode": "shared",  # Default mode
                "show_script_names": False,
                "auto_shuffle_enabled": False,
                "auto_shuffle_interval": 300,
                "dependencies_ready": True,
                "status": "online"  # Set status to online when registering
            }

            # Upsert hub registration (no status field)
            result = self.supabase.table("hubs").upsert(
                hub_data,
                on_conflict="machine_id"
            ).execute()

            self.hub_id = result.data[0]['id']
            self.logger.info(f"[bright_green]Hub registered successfully[/bright_green] [bold]Hub ID:[/bold] [cyan]{self.hub_id}[/cyan]", extra={"markup": True})

            # Update hub_scripts table
            self.update_hub_scripts()

            # Note: Presence will be started after real-time setup to share connection
            return True

        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False

    async def ensure_async_client(self):
        """Ensure async client exists with thread safety"""
        if self._async_client_lock is None:
            self._async_client_lock = asyncio.Lock()
        
        async with self._async_client_lock:
            if not self.async_supabase:
                self.async_supabase = await create_async_client(self.supabase_url, self.supabase_key)
        return self.async_supabase

    async def start_presence_async(self):
        """Start Supabase Presence tracking for online/offline status (async)"""
        try:
            # Ensure async client exists
            await self.ensure_async_client()

            # Create presence channel with proper config
            self.presence_channel = self.async_supabase.channel(
                "hub-presence",
                {
                    "config": {
                        "broadcast": {"ack": False, "self": False},
                        "presence": {"key": self.machine_id},
                        "private": False
                    }
                }
            )

            # Track hub presence
            presence_data = {
                "machine_id": self.machine_id,
                "friendly_name": self.friendly_name,
                "hub_id": self.hub_id,
                "scripts": [s.replace('_', ' ').title() for s in self.available_scripts],
                "script_count": len(self.available_scripts),
                "online_at": datetime.now().isoformat()
            }

            # Subscribe and track presence (async methods)
            await self.presence_channel.subscribe()
            await self.presence_channel.track(presence_data)

            self.logger.info("[OK] Presence tracking active")
            return True

        except Exception as e:
            self.logger.error(f"Presence setup error: {e}")
            return False

    def start_presence(self):
        """Start Supabase Presence tracking (sync wrapper)"""
        try:
            # Run async presence setup
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context, schedule task
                asyncio.create_task(self.start_presence_async())
            else:
                # Create new event loop
                asyncio.run(self.start_presence_async())
            return True
        except Exception as e:
            self.logger.error(f"Presence setup error: {e}")
            return False

    def update_hub_scripts(self):
        """Update the hub_scripts table with available scripts"""
        try:
            # Set up embedded scripts
            self.setup_embedded_scripts()

            # Rediscover scripts (this will install dependencies)
            self.available_scripts = self.discover_scripts()

            # First, delete all existing scripts for this hub to clean up removed ones
            self.supabase.table("hub_scripts").delete().eq("hub_id", self.hub_id).execute()

            # Then insert current scripts
            if self.available_scripts:
                script_records = []
                for script_name in self.available_scripts:
                    # Custom friendly names for better display
                    friendly_name = self.get_friendly_name(script_name)
                    script_records.append({
                        "hub_id": self.hub_id,
                        "script_name": script_name,
                        "friendly_name": friendly_name
                    })
                
                # Insert all current scripts
                self.supabase.table("hub_scripts").insert(script_records).execute()
                
                self.logger.info(f"Updated hub_scripts table with {len(script_records)} scripts")

        except Exception as e:
            self.logger.error(f"Error updating hub scripts: {e}")


    async def execute_script_async_direct(self, script_name: str, remote_id: str) -> Dict[str, Any]:
        """Execute a script using async subprocess (no thread pool bottleneck)"""
        start_time = time.time()

        # Check if script exists
        if script_name not in self.available_scripts:
            return {
                "success": False,
                "error": f"Script not found: {script_name}",
                "duration_ms": 0
            }
        
        # Check if dependencies are ready
        if script_name in self.script_dependencies_ready and not self.script_dependencies_ready[script_name]:
            self.logger.warning(f"[EXEC] Script {script_name} has unresolved dependencies, attempting execution anyway...")

        self.logger.info(f"Executing script '{script_name}' for remote '{remote_id}'")

        try:
            script_dir = self.scripts_dir / script_name

            # Determine script type and path
            if (script_dir / f"{script_name}.py").exists():
                script_path = script_dir / f"{script_name}.py"

                # Set up environment variables for better asset discovery
                env = os.environ.copy()
                env['SCRIPT_DIR'] = str(script_dir)
                env['HUB_ROOT'] = str(Path.home() / "SP-Crew-Hub-Scripts")
                env['ASSETS_DIR'] = str(Path.home() / "SP-Crew-Hub-Scripts" / "assets")

                # Check if script has pyproject.toml for dependencies
                if (script_dir / "pyproject.toml").exists():
                    # Use bundled UV to run with dependencies
                    uv_cmd = self.uv_executable if self.uv_executable else "uv"
                    proc = await asyncio.create_subprocess_exec(
                        uv_cmd, "run", str(script_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=script_dir,
                        env=env,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                    )
                else:
                    # Fallback to direct python execution
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable, str(script_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=script_dir,
                        env=env,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                    )
            elif (script_dir / f"{script_name}.ps1").exists():
                script_path = script_dir / f"{script_name}.ps1"
                proc = await asyncio.create_subprocess_exec(
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
            else:
                return {"success": False, "error": f"Script file not found in directory: {script_name}", "duration_ms": 0}

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
                stdout = stdout.decode('utf-8', errors='replace')
                stderr = stderr.decode('utf-8', errors='replace')
                
                duration_ms = int((time.time() - start_time) * 1000)

                # Enhanced success detection
                success_indicators = [
                    proc.returncode == 0,
                    "success" in stdout.lower(),
                    "completed" in stdout.lower(),
                    "done" in stdout.lower()
                ]
                
                error_indicators = [
                    "error" in stderr.lower(),
                    "failed" in stderr.lower(),
                    "exception" in stderr.lower()
                ]
                
                # Success if return code is 0 OR positive indicators found AND no errors
                is_success = (proc.returncode == 0 or any(success_indicators)) and not any(error_indicators)
                
                execution_result = {
                    "success": is_success,
                    "output": stdout if proc.returncode == 0 else stderr,
                    "duration_ms": duration_ms,
                    "script_name": script_name,
                    "timestamp": datetime.now().isoformat()
                }

                if proc.returncode == 0:
                    self.logger.info(f"[bright_green]{script_name}[/bright_green] [bold]executed successfully[/bold] [dim]({duration_ms}ms)[/dim]", extra={"markup": True})
                else:
                    self.logger.error(f"[bright_red]{script_name}[/bright_red] [bold]failed:[/bold] {stderr}", extra={"markup": True})
                    execution_result["error"] = stderr

                return execution_result

            except asyncio.TimeoutError:
                # Kill the process if it's still running
                if proc.returncode is None:
                    proc.kill()
                    await proc.wait()
                    
                duration_ms = int((time.time() - start_time) * 1000)
                self.logger.error(f"[bright_red]TIMEOUT[/bright_red] [bold]{script_name}[/bold] timed out after 15 seconds", extra={"markup": True})
                return {
                    "success": False,
                    "error": "Script execution timed out (15s limit)",
                    "duration_ms": duration_ms
                }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Async script execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms
            }

    async def execute_script_async(self, script_name: str, user_id: str, command_id: str):
        """Execute a script asynchronously and handle all database operations"""
        try:
            # Update command status to executing
            db_start = time.time()
            self.supabase.table('script_commands').update({
                'status': 'executing'
            }).eq('id', command_id).execute()
            db_duration = int((time.time() - db_start) * 1000)
            self.logger.info(f"[DB] Status update took {db_duration}ms [ID: {command_id}]")
            
            # Execute the script directly with async subprocess (no thread pool bottleneck)
            result = await self.execute_script_async_direct(script_name, user_id)
            final_status = 'completed' if result.get('success') else 'failed'
            
            # Record the result
            result_data = {
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'duration_ms': result.get('duration_ms', 0),
                'script_name': script_name,
                'user_id': user_id
            }
            
            self.supabase.table('script_results').insert({
                'command_id': command_id,
                'exit_code': 0 if result.get('success') else 1,
                'stdout': result.get('output', ''),
                'stderr': result.get('error', ''),
                'success': result.get('success', False),
                'result': result_data  # Required JSONB field
            }).execute()
            
            # Update command status
            self.supabase.table('script_commands').update({
                'status': final_status
            }).eq('id', command_id).execute()
            
            status_text = "[SUCCESS]" if final_status == 'completed' else "[FAILED]"
            self.logger.info(f"{status_text} Command {final_status}: {script_name} [ID: {command_id}]")
            
        except Exception as e:
            self.logger.error(f"Async script execution error for {command_id}: {e}")
            # Try to mark the command as failed
            try:
                self.supabase.table('script_commands').update({
                    'status': 'failed'
                }).eq('id', command_id).execute()
            except:
                self.logger.error(f"Could not update command status for {command_id} - command may be stuck")

    def handle_execute_message(self, payload):
        """Handle script execution message from real-time channel"""
        try:
            receive_time = datetime.now(timezone.utc)
            self.logger.debug(f"Received real-time message: {payload}")
            # Extract data from the correct location in the payload
            data = payload.get('data', {}).get('record', {})
            script_name = data.get('script_name')
            user_id = data.get('user_id')
            command_id = data.get('id')
            status = data.get('status', 'pending')
            created_at = data.get('created_at')

            # Calculate real-time latency if we have creation timestamp
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if created_time.tzinfo is None:
                        created_time = created_time.replace(tzinfo=timezone.utc)
                    latency_ms = int((receive_time - created_time).total_seconds() * 1000)
                    self.logger.info(f"[TIMING] Real-time latency: {latency_ms}ms for {script_name}")
                except Exception as e:
                    self.logger.debug(f"Could not calculate latency: {e}")

            self.logger.debug(f"Processing command: script={script_name}, id={command_id}, status={status}")

            if not script_name or not command_id or status != 'pending':
                self.logger.warning(f"Skipping command - missing data or wrong status")
                return

            # Check for duplicate command execution
            if command_id in self.processed_commands:
                self.logger.warning(f"Skipping duplicate command ID: {command_id}")
                return
            
            # Mark command as processed
            self.processed_commands.add(command_id)

            # Execute script asynchronously to allow concurrent execution
            self.logger.info(f"[bright_blue]🚀[/bright_blue] [bold]Spawning async task[/bold] for [cyan]{script_name}[/cyan] [dim]\\[ID: {command_id}\\][/dim]", extra={"markup": True})
            asyncio.create_task(self.execute_script_async(script_name, user_id or 'unknown', command_id))

        except Exception as e:
            self.logger.error(f"Error handling execute message: {e}")

    def assign_script_to_remote(self, user_id: str) -> tuple[Optional[str], Optional[str]]:
        """Assign a random script to a remote user"""
        try:
            if not self.available_scripts:
                self.logger.warning("No scripts available to assign")
                return None, None

            # Simple random assignment
            selected_script = random.choice(self.available_scripts)
            script_color = f"#{random.randint(0x100000, 0xFFFFFF):06x}"

            # Update active_remotes table
            self.supabase.table('active_remotes').upsert({
                'hub_id': self.hub_id,
                'user_id': user_id,
                'assigned_script': selected_script,
                'script_color': script_color,
                'last_seen': datetime.now().isoformat() + 'Z'
            }, on_conflict='hub_id,user_id').execute()

            self.logger.info(f"Assigned script '{selected_script}' to user {user_id}")
            return selected_script, script_color

        except Exception as e:
            self.logger.error(f"Error assigning script to user {user_id}: {e}")
            return None, None

    def handle_remote_connection(self, payload):
        """Handle new remote connections in assigned mode"""
        try:
            # Extract data from the correct location in the payload
            data = payload.get('data', {}).get('record', {})
            if data.get('hub_id') == self.hub_id:
                user_id = data.get('user_id')

                # Get hub mode
                hub_data = self.supabase.table('hubs').select('mode').eq('id', self.hub_id).single().execute()

                # Only assign scripts in assigned mode and if no script assigned yet
                if hub_data.data.get('mode') == 'assigned' and not data.get('assigned_script'):
                    self.assign_script_to_remote(user_id)
        except Exception as e:
            self.logger.error(f"Error handling remote connection: {e}")

    async def setup_realtime_channel(self):
        """Setup Supabase real-time channel for listening to commands"""
        try:
            # Ensure async client exists
            await self.ensure_async_client()

            # Create channel with error callback
            self.channel = self.async_supabase.channel(f"hub-{self.hub_id}")
            
            # Note: AsyncRealtimeChannel doesn't support on_error/on_close callbacks
            # WebSocket errors will be handled through try/catch blocks

            # Listen for new script execution commands targeting this hub
            self.channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="script_commands",
                filter=f"hub_id=eq.{self.hub_id}",
                callback=self.handle_execute_message
            )

            # Listen for remote connections in assigned mode
            self.channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="active_remotes",
                filter=f"hub_id=eq.{self.hub_id}",
                callback=self.handle_remote_connection
            )

            self.channel.on_postgres_changes(
                event="UPDATE",
                schema="public",
                table="active_remotes",
                filter=f"hub_id=eq.{self.hub_id}",
                callback=self.handle_remote_connection
            )

            # Subscribe to the channel
            await self.channel.subscribe()

            self.logger.info("[OK] Real-time messaging connected")
            self.reconnect_attempts = 0  # Reset on successful connection

        except Exception as e:
            self.logger.error(f"Error setting up real-time channel: {e}")
            raise

    def handle_websocket_error(self, error):
        """Handle WebSocket errors"""
        self.logger.error(f"[ERROR] WebSocket error: {error}")
        # Trigger reconnection
        asyncio.create_task(self.reconnect_websocket())

    def handle_websocket_close(self, code, reason):
        """Handle WebSocket connection close"""
        self.logger.warning(f"[WARN] WebSocket closed [Code: {code}] {reason or 'No reason given'}")
        # Trigger reconnection unless shutting down
        if self.running:
            asyncio.create_task(self.reconnect_websocket())

    async def reconnect_websocket(self):
        """Attempt to reconnect WebSocket with exponential backoff"""
        if not self.running:
            return
            
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > self.max_reconnect_attempts:
            self.logger.error(f"[ERROR] Max reconnection attempts ({self.max_reconnect_attempts}) reached. Hub going offline.")
            self.running = False
            return
        
        # Exponential backoff: 2^attempt seconds (max 60s)
        delay = min(2 ** self.reconnect_attempts, 60)
        self.logger.info(f"🔄 Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay}s...")
        
        await asyncio.sleep(delay)
        
        try:
            # Clean up old connections
            if self.channel:
                try:
                    await self.channel.unsubscribe()
                except:
                    pass
            if self.presence_channel:
                try:
                    await self.presence_channel.unsubscribe()
                except:
                    pass
            
            # Reset async client
            self.async_supabase = None
            
            # Reconnect both channels
            await self.setup_realtime_channel()
            await self.start_presence_async()
            
            self.logger.info("[OK] WebSocket reconnection successful!")
            
        except Exception as e:
            self.logger.error(f"[ERROR] Reconnection failed: {e}")
            # Try again
            asyncio.create_task(self.reconnect_websocket())

    def start_heartbeat_thread(self):
        """Start heartbeat thread to maintain online status"""
        def heartbeat():
            self.logger.debug("[HEARTBEAT] Starting heartbeat loop")
            while self.running:
                try:
                    # Update status to online with current UTC timestamp 
                    current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    self.supabase.table('hubs').update({
                        'status': 'online',
                        'last_seen': current_time
                    }).eq('id', self.hub_id).execute()
                    
                    self.logger.debug(f"[HEARTBEAT] Updated last_seen to {current_time}")
                    time.sleep(30)  # 30 second heartbeat interval
                except Exception as e:
                    self.logger.error(f"[HEARTBEAT] Heartbeat error: {e}")
                    time.sleep(30)  # Retry delay on error
            
            self.logger.debug("[HEARTBEAT] Heartbeat loop ended")
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        self.logger.info("[bright_green]Status heartbeat started[/bright_green]", extra={"markup": True})

    async def run_async(self):
        """Start the Hub Worker service (headless) with async real-time"""
        self.console.print("\n[bold blue]Starting Hub Worker (headless mode)...[/bold blue]", style="bold")

        # Register with Supabase
        if not self.register_hub():
            self.logger.error("Failed to register hub. Exiting.")
            return

        # Setup real-time messaging and presence (single connection)
        await self.setup_realtime_channel()
        await self.start_presence_async()

        # Start heartbeat thread
        self.start_heartbeat_thread()

        # Rich ready panel
        hotkey_ready = f"[red]Emergency Shutdown:[/red] [yellow]{self.emergency_hotkey.upper()}[/yellow]" if HOTKEY_AVAILABLE else "[dim]Emergency Shutdown: Not Available[/dim]"
        ready_panel = Panel.fit(
            f"[bold green]HUB WORKER IS ONLINE AND READY![/bold green]\n\n"
            f"[bright_green]Real-time messaging:[/bright_green] [green]Connected[/green]\n"
            f"[bright_green]Presence tracking:[/bright_green] [green]Active[/green]\n"
            f"[bright_green]Status heartbeat:[/bright_green] [green]Running[/green]\n"
            f"{hotkey_ready}\n\n"
            f"[dim]Waiting for script execution commands...[/dim]",
            title="[bold bright_green]READY FOR COMMANDS[/bold bright_green]",
            border_style="bright_green"
        )
        self.console.print(ready_panel)

        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down Hub Worker...")
            self.running = False

            # Cleanup connections and set offline status
            await self.cleanup_connections()

    async def cleanup_connections(self):
        """Clean up all connections and set hub offline"""
        try:
            # Close WebSocket connections
            if self.channel:
                await self.channel.unsubscribe()
                self.logger.info("[OK] Real-time channel unsubscribed")
            
            if self.presence_channel:
                await self.presence_channel.unsubscribe()
                self.logger.info("[OK] Presence channel unsubscribed")
            
            # Close async client
            if self.async_supabase:
                # Note: Supabase client doesn't have explicit close method
                self.async_supabase = None
            
            # Update status to offline using sync client
            if self.hub_id:
                self.supabase.table('hubs').update({
                    'status': 'offline'
                }).eq('id', self.hub_id).execute()
                self.logger.info("[OK] Hub status set to offline")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Wrapper to run the async version"""
        asyncio.run(self.run_async())

def main():
    """Entry point for the hub application"""
    hub = HubWorker()
    hub.run()

if __name__ == "__main__":
    main()
