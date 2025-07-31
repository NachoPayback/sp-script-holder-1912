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

# Add project root to path for script imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class HubWorker:
    def __init__(self):
        self.setup_logging()

        # Hub configuration
        self.machine_id = self.get_machine_id()
        self.hub_id = None  # Will be set after registration
        self.friendly_name = f"Hub-{socket.gethostname()}"

        # Load Supabase configuration
        config_path = Path(__file__).parent.parent / "config" / "supabase.json"
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

        self.logger.info(f"Hub Worker initialized [ID: {self.machine_id}] - Found {len(self.available_scripts)} scripts")

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
            self.logger.info(f"[DEPS] Installing dependencies for {script_name}...")
            
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
                self.logger.info(f"[DEPS] ✓ Dependencies ready for {script_name}")
                self.script_dependencies_ready[script_name] = True
                return True
            else:
                self.logger.error(f"[DEPS] ✗ Failed to install dependencies for {script_name}:")
                self.logger.error(f"[DEPS]   {result.stderr.strip()}")
                self.script_dependencies_ready[script_name] = False
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"[DEPS] ✗ Timeout installing dependencies for {script_name}")
            self.script_dependencies_ready[script_name] = False
            return False
        except Exception as e:
            self.logger.error(f"[DEPS] ✗ Error installing dependencies for {script_name}: {e}")
            self.script_dependencies_ready[script_name] = False
            return False

    def pull_latest_scripts(self):
        """Pull latest scripts from git repository (scripts directory only)"""
        try:
            self.logger.debug("Pulling latest scripts from repository...")
            
            # Use sparse checkout to only pull scripts directory
            # First, ensure sparse checkout is enabled
            subprocess.run(
                ["git", "config", "core.sparseCheckout", "true"],
                cwd=project_root,
                capture_output=True,
                timeout=10
            )
            
            # Set sparse checkout to include scripts directory (includes all subdirs and pyproject.toml files)
            sparse_checkout_file = project_root / ".git" / "info" / "sparse-checkout"
            with open(sparse_checkout_file, 'w') as f:
                f.write("scripts/\n")  # Includes all script files, subdirectories, and pyproject.toml files
            
            # Pull only the scripts directory
            result = subprocess.run(
                ["git", "pull", "origin", "master"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.debug("Successfully pulled latest scripts")
            else:
                self.logger.warning(f"Git pull failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Error pulling latest scripts: {e}")

    def setup_logging(self):
        """Setup logging configuration with reduced verbosity"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"hub_worker_{datetime.now().strftime('%Y%m%d')}.log"

        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',  # Simplified format
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Configure stdout to handle Unicode on Windows
        if sys.stdout.encoding != 'utf-8':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        
        # Reduce verbosity of noisy libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)  # Only show HTTP errors
        logging.getLogger('realtime._async.client').setLevel(logging.WARNING)  # Only show WebSocket errors
        logging.getLogger('supabase').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger('HubWorker')

    def get_machine_id(self) -> str:
        """Generate consistent machine ID based on hardware"""
        # Combine hostname and platform info for a stable ID
        machine_info = f"{socket.gethostname()}-{platform.machine()}-{platform.processor()}"
        return hashlib.sha256(machine_info.encode()).hexdigest()[:16]

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
        self.logger.info(f"[DISCOVERY] Found {len(scripts)} scripts, {ready_count} with dependencies ready")

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
            self.logger.info(f"[OK] Hub registered successfully [Hub ID: {self.hub_id}]")

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
                    # Convert folder name to friendly display name
                    friendly_name = script_name.replace('_', ' ').title()
                    script_records.append({
                        "hub_id": self.hub_id,
                        "script_name": script_name,
                        "friendly_name": friendly_name
                    })
                
                # Single batch insert instead of individual calls
                self.supabase.table("hub_scripts").insert(script_records).execute()

        except Exception as e:
            self.logger.error(f"Error updating hub scripts: {e}")

    def execute_script(self, script_name: str, remote_id: str) -> Dict[str, Any]:
        """Execute a script and return results"""
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
            # Try to install dependencies one more time
            script_dir = self.scripts_dir / script_name
            if script_dir.exists():
                self.install_script_dependencies(script_dir)

        self.logger.info(f"Executing script '{script_name}' for remote '{remote_id}'")

        try:
            script_dir = self.scripts_dir / script_name

            # Determine script type and path
            if (script_dir / f"{script_name}.py").exists():
                script_path = script_dir / f"{script_name}.py"

                # Check if script has pyproject.toml for dependencies
                if (script_dir / "pyproject.toml").exists():
                    # Use UV to run with dependencies
                    result = subprocess.run(
                        ["uv", "run", str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=script_dir
                    )
                else:
                    # Fallback to direct python execution
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=script_dir
                    )
            elif (script_dir / f"{script_name}.ps1").exists():
                script_path = script_dir / f"{script_name}.ps1"
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=script_dir
                )
            else:
                return {"success": False, "error": f"Script file not found in directory: {script_name}", "duration_ms": 0}

            duration_ms = int((time.time() - start_time) * 1000)

            # Enhanced success detection
            success_indicators = [
                result.returncode == 0,
                "success" in result.stdout.lower(),
                "completed" in result.stdout.lower(),
                "done" in result.stdout.lower()
            ]
            
            error_indicators = [
                "error" in result.stderr.lower(),
                "failed" in result.stderr.lower(),
                "exception" in result.stderr.lower()
            ]
            
            # Success if return code is 0 OR positive indicators found AND no errors
            is_success = (result.returncode == 0 or any(success_indicators)) and not any(error_indicators)
            
            execution_result = {
                "success": is_success,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "duration_ms": duration_ms,
                "script_name": script_name,
                "timestamp": datetime.now().isoformat()
            }

            if result.returncode == 0:
                self.logger.info(f"[SUCCESS] {script_name} executed successfully ({duration_ms}ms)")
            else:
                self.logger.error(f"Script '{script_name}' failed: {result.stderr}")
                execution_result["error"] = result.stderr

            return execution_result

        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Script '{script_name}' timed out after 30 seconds")
            return {
                "success": False,
                "error": "Script execution timed out (30s limit)",
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Script execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration_ms
            }

    def handle_execute_message(self, payload):
        """Handle script execution message from real-time channel"""
        try:
            self.logger.info(f"Received real-time message: {payload}")
            # Extract data from the correct location in the payload
            data = payload.get('data', {}).get('record', {})
            script_name = data.get('script_name')
            user_id = data.get('user_id')
            command_id = data.get('id')
            status = data.get('status', 'pending')

            self.logger.debug(f"Processing command: script={script_name}, id={command_id}, status={status}")

            if not script_name or not command_id or status != 'pending':
                self.logger.warning(f"Skipping command - missing data or wrong status")
                return

            # Execute script with comprehensive error handling
            result = None
            final_status = 'failed'
            
            try:
                # Update command status to executing
                self.supabase.table('script_commands').update({
                    'status': 'executing'
                }).eq('id', command_id).execute()
                
                # Execute the script
                result = self.execute_script(script_name, user_id or 'unknown')
                final_status = 'completed' if result.get('success') else 'failed'
                
            except Exception as db_error:
                self.logger.error(f"Database error during command execution: {db_error}")
                result = {
                    'success': False,
                    'error': f'Database error: {str(db_error)}',
                    'output': '',
                    'duration_ms': 0
                }
                final_status = 'failed'
            
            # Always try to record the result, even if script execution failed
            try:
                # Insert result with required JSONB result field
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
                
            except Exception as result_error:
                self.logger.error(f"Failed to record result for command {command_id}: {result_error}")
                # Try to at least mark the command as failed
                try:
                    self.supabase.table('script_commands').update({
                        'status': 'failed'
                    }).eq('id', command_id).execute()
                except:
                    self.logger.error(f"Could not update command status for {command_id} - command may be stuck")

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
            self.logger.info("[HEARTBEAT] Starting heartbeat loop")
            while self.running:
                try:
                    # Update status to online with current UTC timestamp 
                    current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    self.supabase.table('hubs').update({
                        'status': 'online',
                        'last_seen': current_time
                    }).eq('id', self.hub_id).execute()
                    
                    self.logger.info(f"[HEARTBEAT] Updated last_seen to {current_time}")
                    time.sleep(10)  # Reduced to 10 seconds for testing
                except Exception as e:
                    self.logger.error(f"[HEARTBEAT] Heartbeat error: {e}")
                    time.sleep(10)  # Longer retry delay
            
            self.logger.info("[HEARTBEAT] Heartbeat loop ended")
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        self.logger.info("[OK] Status heartbeat started")

    async def run_async(self):
        """Start the Hub Worker service (headless) with async real-time"""
        self.logger.info("Starting Hub Worker (headless mode)")

        # Register with Supabase
        if not self.register_hub():
            self.logger.error("Failed to register hub. Exiting.")
            return

        # Setup real-time messaging and presence (single connection)
        await self.setup_realtime_channel()
        await self.start_presence_async()

        # Start heartbeat thread
        self.start_heartbeat_thread()

        self.logger.info("[READY] Hub Worker is ONLINE and ready for commands!")

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

if __name__ == "__main__":
    hub = HubWorker()
    hub.run()
