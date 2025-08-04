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

from supabase import Client, create_client
from supabase._async.client import create_client as create_async_client
import git

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

# Configuration for standalone hub
GITHUB_REPO_URL = "https://github.com/NachoPayback/P-Buttons.git"
WORKING_DIR = Path(__file__).parent.parent  # Use current project directory

# Add project root to path for script imports
project_root = WORKING_DIR
sys.path.insert(0, str(project_root))

class HubWorker:
    def __init__(self):
        self.setup_logging()
        
        # Ensure working directory exists
        self.setup_working_directory()

        # Hub configuration
        self.machine_id = self.get_machine_id()
        self.hub_id = None  # Will be set after registration
        self.friendly_name = f"Hub-{socket.gethostname()}"

        # Load Supabase configuration
        config_path = Path(__file__).parent / "config" / "supabase.json"
        with open(config_path, 'r') as f:
            supabase_config = json.load(f)

        self.supabase_url = supabase_config["url"]
        self.supabase_key = supabase_config["anon_key"]
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.async_supabase = None  # Single async client for all real-time operations
        self._async_client_lock = None  # Will be created in async context

        # Script management
        self.scripts_dir = project_root / "scripts"
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

        # Rich startup banner
        startup_panel = Panel.fit(
            f"[bold blue]SP CREW CONTROL V2 - HUB WORKER[/bold blue]\n"
            f"[dim]Pure script execution engine using Supabase real-time messaging[/dim]\n\n"
            f"[green]Machine ID:[/green] [cyan]{self.machine_id}[/cyan]\n"
            f"[green]Scripts Found:[/green] [yellow]{len(self.available_scripts)}[/yellow]\n"
            f"[green]Dependencies Ready:[/green] [yellow]{sum(1 for ready in self.script_dependencies_ready.values() if ready)}[/yellow]",
            title="[bold green]INITIALIZATION COMPLETE[/bold green]",
            border_style="green"
        )
        if platform.system() != "Windows":  # Only show rich panels on non-Windows
            self.console.print(startup_panel)

    def setup_logging(self):
        """Setup logging - plain logging for Windows to avoid encoding issues"""
        if platform.system() == "Windows":
            self.console = Console(force_terminal=False)
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S"
            )
        else:
            self.console = Console(force_terminal=True)
            logging.basicConfig(
                level=logging.INFO,
                format="%(message)s",
                datefmt="[%X]",
                handlers=[RichHandler(rich_tracebacks=True, console=self.console)]
            )
        self.logger = logging.getLogger("hub")

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
                    ["uv", "venv"],
                    cwd=script_dir,
                    capture_output=True,
                    timeout=30
                )
                
                # Install dependencies from pyproject.toml
                result = subprocess.run(
                    ["uv", "pip", "install", "-e", "."],
                    cwd=script_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                # Use inline script dependencies (PEP 723) 
                result = subprocess.run(
                    ["uv", "run", script_py_path.name, "--help"],  # This will install deps
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
        """Setup working directory and ensure uv is available"""
        try:
            # Ensure uv is installed first
            self.ensure_uv_installed()
            
            # We're using the current project directory
            self.console.print(f"[blue]Using project directory: {WORKING_DIR}[/blue]")
                
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
        """Ensure uv is installed and available"""
        try:
            # Check if uv is already available
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print(f"[green]uv is already installed: {result.stdout.strip()}[/green]")
                return
        except FileNotFoundError:
            pass
        
        # Install uv
        self.console.print("[yellow]Installing uv package manager...[/yellow]")
        
        try:
            if platform.system() == "Windows":
                # Use PowerShell to install uv on Windows
                result = subprocess.run([
                    "powershell", "-Command",
                    "irm https://astral.sh/uv/install.ps1 | iex"
                ], capture_output=True, text=True, timeout=120)
            else:
                # Use curl for Unix-like systems
                result = subprocess.run([
                    "sh", "-c",
                    "curl -LsSf https://astral.sh/uv/install.sh | sh"
                ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.console.print("[green]uv installed successfully![/green]")
                
                # Verify installation
                result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.console.print(f"[green]uv version: {result.stdout.strip()}[/green]")
                else:
                    # Try adding to PATH for current session
                    if platform.system() == "Windows":
                        uv_path = Path.home() / ".cargo" / "bin"
                    else:
                        uv_path = Path.home() / ".local" / "bin"
                    
                    if uv_path.exists():
                        os.environ["PATH"] = str(uv_path) + os.pathsep + os.environ.get("PATH", "")
                        self.console.print(f"[yellow]Added {uv_path} to PATH[/yellow]")
            else:
                raise Exception(f"Installation failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Failed to install uv: {e}")
            self.console.print("[red]Failed to install uv. Please install manually from https://docs.astral.sh/uv/getting-started/installation/[/red]")
            raise

    def pull_latest_scripts(self):
        """Pull latest scripts from git repository using GitPython (scripts directory only)"""
        try:
            self.logger.debug("Pulling latest scripts from repository...")
            
            # Open the git repository
            repo = git.Repo(project_root)
            
            # Pull latest changes from origin/master
            origin = repo.remotes.origin
            origin.pull('master')
            
            self.logger.debug("Successfully pulled latest scripts using GitPython")
                
        except Exception as e:
            self.logger.error(f"Error pulling latest scripts: {e}")

    def setup_logging(self):
        """Setup Rich logging with beautiful colors and formatting"""
        # Note: Can't use WORKING_DIR here as it's called before setup_working_directory
        log_dir = Path.home() / ".sp-crew-hub" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"hub_worker_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create Rich console
        self.console = Console()
        
        # Configure Rich logging
        rich_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        
        # Create file handler with proper formatter
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',  # Rich handles the formatting
            handlers=[
                file_handler,
                rich_handler
            ]
        )
        
        # Reduce verbosity of noisy libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('realtime._async.client').setLevel(logging.WARNING)
        logging.getLogger('supabase').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger('HubWorker')

    def get_machine_id(self) -> str:
        """Generate consistent machine ID based on hardware"""
        # Combine hostname and platform info for a stable ID
        machine_info = f"{socket.gethostname()}-{platform.machine()}-{platform.processor()}"
        return hashlib.sha256(machine_info.encode()).hexdigest()[:16]

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
            # Pull latest scripts from git
            self.pull_latest_scripts()

            # Rediscover scripts (this will install dependencies)
            self.available_scripts = self.discover_scripts()

            # Clear existing scripts for this hub
            self.supabase.table("hub_scripts").delete().eq("hub_id", self.hub_id).execute()

            # Insert current scripts in batch
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
                
                # Single batch insert instead of individual calls
                self.supabase.table("hub_scripts").insert(script_records).execute()

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

                # Check if script has pyproject.toml for dependencies
                if (script_dir / "pyproject.toml").exists():
                    # Use UV to run with dependencies
                    proc = await asyncio.create_subprocess_exec(
                        "uv", "run", str(script_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=script_dir
                    )
                else:
                    # Fallback to direct python execution
                    proc = await asyncio.create_subprocess_exec(
                        sys.executable, str(script_path),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=script_dir
                    )
            elif (script_dir / f"{script_name}.ps1").exists():
                script_path = script_dir / f"{script_name}.ps1"
                proc = await asyncio.create_subprocess_exec(
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=script_dir
                )
            else:
                return {"success": False, "error": f"Script file not found in directory: {script_name}", "duration_ms": 0}

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15.0)
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
                self.logger.error(f"[bright_red]⏱[/bright_red] [bold]{script_name}[/bold] timed out after 15 seconds", extra={"markup": True})
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
        ready_panel = Panel.fit(
            f"[bold green]HUB WORKER IS ONLINE AND READY![/bold green]\n\n"
            f"[bright_green]Real-time messaging:[/bright_green] [green]Connected[/green]\n"
            f"[bright_green]Presence tracking:[/bright_green] [green]Active[/green]\n"
            f"[bright_green]Status heartbeat:[/bright_green] [green]Running[/green]\n\n"
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
