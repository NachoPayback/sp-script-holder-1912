#!/usr/bin/env python3
"""
SP Crew Hub V3 - Simplified and Clean
Syncs executables from GitHub and executes them via Supabase commands
"""

import asyncio
import hashlib
import json
import logging
import os
import platform
import random
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Emergency shutdown hotkey support
try:
    import keyboard
    HOTKEY_AVAILABLE = True
except ImportError:
    HOTKEY_AVAILABLE = False

from supabase import Client, create_client
from supabase._async.client import create_client as create_async_client

# Rich console for pretty output
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

# Import our program sync module - use bundled version
from program_sync_bundled import ProgramSync


class SPCrewHub:
    def __init__(self, silent_mode: bool = False):
        self.silent_mode = silent_mode
        self.setup_logging()
        
        # Hub identification
        self.machine_id = self.get_machine_id()
        self.hub_id = None
        self.friendly_name = f"Hub-{socket.gethostname()}"
        
        # Supabase configuration
        self.supabase_url = "https://qcefzjjxnwccjivsbtgb.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4"
        
        # Fix SSL certificate issues
        import ssl
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        
        # Create Supabase clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.async_supabase = None
        
        # Program management
        self.program_sync = ProgramSync(self.logger)
        self.available_programs: List[str] = []
        
        # Real-time messaging
        self.channel = None
        self.presence_channel = None
        self.processed_commands = set()
        
        # State
        self.running = True
        self.shutdown_requested = False
        
        # Emergency shutdown
        self.setup_emergency_shutdown()
        
        # Show startup banner
        if not self.silent_mode:
            self.show_startup_banner()
    
    def setup_logging(self):
        """Setup logging with Rich console"""
        self.console = Console() if not self.silent_mode else None
        
        # Log file location - hidden with programs or nowhere for silent
        log_file = None
        if not self.silent_mode:
            log_file = "sp_crew_hub.log"
        else:
            # Silent mode: log to programs directory if it exists, otherwise no file
            programs_dir = Path.home() / "SP-Crew-Hub" / "programs"
            if programs_dir.exists():
                log_file = programs_dir / ".hub.log"  # Hidden file
        
        handlers = []
        
        # Console handler only for terminal mode
        if not self.silent_mode:
            handlers.append(RichHandler(
                console=self.console, 
                rich_tracebacks=True, 
                markup=True,  # Enable markup for colors
                show_path=False,
                show_time=False  # We'll handle time in format
            ))
        
        # File handler if we have a log file
        if log_file:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        
        # Silent mode gets no output at all if no handlers
        if not handlers and self.silent_mode:
            handlers.append(logging.NullHandler())
        
        log_level = logging.CRITICAL if self.silent_mode else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format="[%(asctime)s] %(message)s" if not self.silent_mode else "%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
            force=True  # Override any existing config
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Suppress noisy Supabase realtime logs
        logging.getLogger("realtime").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.WARNING)
        logging.getLogger("supabase").setLevel(logging.WARNING)
        
        # Create custom filter for remaining messages
        class CleanupFilter(logging.Filter):
            def filter(self, record):
                # Hide raw JSON receive/send messages
                if "receive:" in record.getMessage() and "{" in record.getMessage():
                    return False
                if "send:" in record.getMessage() and "{" in record.getMessage():
                    return False
                return True
        
        # Add filter to all handlers
        cleanup_filter = CleanupFilter()
        for handler in logging.root.handlers:
            handler.addFilter(cleanup_filter)
    
    def setup_emergency_shutdown(self):
        """Setup emergency shutdown hotkey"""
        if not HOTKEY_AVAILABLE or self.silent_mode:
            return
            
        def emergency_shutdown():
            self.logger.warning("EMERGENCY SHUTDOWN TRIGGERED")
            self.console.print("\n[bold red]EMERGENCY SHUTDOWN[/bold red]")
            self.running = False
            self.shutdown_requested = True
            threading.Timer(2.0, lambda: os._exit(0)).start()
        
        try:
            keyboard.add_hotkey("ctrl+shift+q", emergency_shutdown)
        except Exception as e:
            self.logger.warning(f"Could not setup emergency hotkey: {e}")
    
    def get_machine_id(self) -> str:
        """Generate unique machine ID"""
        try:
            hostname = socket.gethostname()
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            machine_string = f"{hostname}-{mac}"
            return hashlib.md5(machine_string.encode()).hexdigest()[:16]
        except Exception:
            fallback = f"{socket.gethostname()}-{random.randint(1000, 9999)}"
            return hashlib.md5(fallback.encode()).hexdigest()[:16]
    
    def show_startup_banner(self):
        """Show startup banner"""
        hotkey_text = "[red]Emergency Shutdown:[/red] [yellow]CTRL+SHIFT+Q[/yellow]" if HOTKEY_AVAILABLE else "[dim]Emergency Shutdown: Not Available[/dim]"
        
        banner = Panel.fit(
            f"[bold blue]SP CREW HUB V3[/bold blue]\n"
            f"[dim]Clean and simple executable runner[/dim]\n\n"
            f"[green]Machine ID:[/green] [cyan]{self.machine_id}[/cyan]\n"
            f"{hotkey_text}",
            title="[bold green]INITIALIZING[/bold green]",
            border_style="green"
        )
        self.console.print(banner)
    
    async def sync_programs(self) -> bool:
        """Sync programs from GitHub"""
        self.logger.info("[yellow]Syncing programs from GitHub...[/yellow]")
        success = self.program_sync.sync_programs()
        
        if success:
            self.available_programs = self.program_sync.get_available_programs()
            self.logger.info(f"[green]Programs synced:[/green] [yellow]{len(self.available_programs)}[/yellow]")
        
        return success
    
    def register_hub(self) -> bool:
        """Register hub with Supabase"""
        try:
            hub_data = {
                "machine_id": self.machine_id,
                "friendly_name": self.friendly_name,
                "mode": "shared",
                "show_script_names": False,
                "auto_shuffle_enabled": False,
                "auto_shuffle_interval": 300,
                "dependencies_ready": True,
                "status": "online"
            }
            
            result = self.supabase.table("hubs").upsert(
                hub_data, on_conflict="machine_id"
            ).execute()
            
            self.hub_id = result.data[0]['id']
            self.logger.info(f"[green]Hub registered[/green]")
            
            # Update hub_scripts table
            self.update_hub_scripts()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return False
    
    def update_hub_scripts(self):
        """Update hub_scripts table with available programs"""
        try:
            # Delete existing scripts
            self.supabase.table("hub_scripts").delete().eq("hub_id", self.hub_id).execute()
            
            # Insert current programs
            if self.available_programs:
                script_records = []
                for program_name in self.available_programs:
                    friendly_name = program_name.replace('_', ' ').title()
                    script_records.append({
                        "hub_id": self.hub_id,
                        "script_name": program_name,
                        "friendly_name": friendly_name
                    })
                
                self.supabase.table("hub_scripts").insert(script_records).execute()
                self.logger.info(f"[green]Scripts available:[/green] [yellow]{len(script_records)}[/yellow]")
                
        except Exception as e:
            self.logger.error(f"Failed to update hub scripts: {e}")
    
    async def ensure_async_client(self):
        """Ensure async Supabase client exists"""
        if not self.async_supabase:
            self.async_supabase = await create_async_client(self.supabase_url, self.supabase_key)
        return self.async_supabase
    
    async def setup_realtime_channel(self):
        """Setup real-time channel for commands"""
        try:
            await self.ensure_async_client()
            
            self.channel = self.async_supabase.channel(f"hub-{self.hub_id}")
            
            # Listen for script execution commands
            self.channel.on_postgres_changes(
                event="INSERT",
                schema="public", 
                table="script_commands",
                filter=f"hub_id=eq.{self.hub_id}",
                callback=self.handle_execute_command
            )
            
            # Listen for remote connections
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
            
            await self.channel.subscribe()
            self.logger.info("[green]Real-time:[/green] [bright_green]Connected[/bright_green]")
            
        except Exception as e:
            self.logger.error(f"Failed to setup real-time: {e}")
            raise
    
    async def start_presence(self):
        """Start presence tracking"""
        try:
            await self.ensure_async_client()
            
            presence_data = {
                "machine_id": self.machine_id,
                "friendly_name": self.friendly_name,
                "hub_id": self.hub_id,
                "scripts": [p.replace('_', ' ').title() for p in self.available_programs],
                "script_count": len(self.available_programs),
                "online_at": datetime.now().isoformat()
            }
            
            self.presence_channel = self.async_supabase.channel(
                "hub-presence",
                {"config": {"presence": {"key": self.machine_id}}}
            )
            
            # Subscribe first and wait for confirmation
            await self.presence_channel.subscribe()
            
            # Small delay to ensure subscription is established
            await asyncio.sleep(0.1)
            
            # Now track presence data
            await self.presence_channel.track(presence_data)
            
            # Send periodic presence updates every 30 seconds
            asyncio.create_task(self._maintain_presence())
            
            self.logger.info("[green]Presence:[/green] [bright_green]Online[/bright_green]")
            
        except Exception as e:
            self.logger.error(f"Failed to start presence: {e}")
    
    async def _maintain_presence(self):
        """Maintain presence with periodic updates"""
        while self.running:
            try:
                await asyncio.sleep(30)
                if self.presence_channel and self.running:
                    presence_data = {
                        "machine_id": self.machine_id,
                        "friendly_name": self.friendly_name,
                        "hub_id": self.hub_id,
                        "scripts": [p.replace('_', ' ').title() for p in self.available_programs],
                        "script_count": len(self.available_programs),
                        "online_at": datetime.now().isoformat()
                    }
                    await self.presence_channel.track(presence_data)
            except Exception as e:
                self.logger.error(f"Presence maintenance error: {e}")
                break
    
    def handle_execute_command(self, payload):
        """Handle script execution command"""
        try:
            data = payload.get('data', {}).get('record', {})
            script_name = data.get('script_name')
            command_id = data.get('id')
            user_id = data.get('user_id')
            status = data.get('status', 'pending')
            
            if not script_name or not command_id or status != 'pending':
                return
                
            if command_id in self.processed_commands:
                self.logger.warning(f"Duplicate command: {command_id}")
                return
                
            self.processed_commands.add(command_id)
            
            self.logger.info(f"[blue]🚀 Executing:[/blue] [cyan]{script_name}[/cyan] [dim]\\[{command_id}\\][/dim]")
            asyncio.create_task(self.execute_program_async(script_name, user_id, command_id))
            
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
    
    def handle_remote_connection(self, payload):
        """Handle new remote connections and assign scripts"""
        try:
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
    
    def assign_script_to_remote(self, user_id: str) -> tuple[Optional[str], Optional[str]]:
        """Assign a random script to a remote user"""
        try:
            if not self.available_programs:
                self.logger.warning("No programs available to assign")
                return None, None

            # Simple random assignment
            selected_script = random.choice(self.available_programs)
            script_color = f"#{random.randint(0x100000, 0xFFFFFF):06x}"

            # Update active_remotes table
            self.supabase.table('active_remotes').upsert({
                'hub_id': self.hub_id,
                'user_id': user_id,
                'assigned_script': selected_script,
                'script_color': script_color,
                'last_seen': datetime.now().isoformat() + 'Z'
            }, on_conflict='hub_id,user_id').execute()

            self.logger.info(f"[blue]Assigned:[/blue] [cyan]{selected_script}[/cyan] to user [yellow]{user_id}[/yellow]")
            return selected_script, script_color

        except Exception as e:
            self.logger.error(f"Error assigning script to user {user_id}: {e}")
            return None, None
    
    async def execute_program_async(self, program_name: str, user_id: str, command_id: str):
        """Execute program asynchronously without blocking"""
        try:
            # Spawn the program FIRST (fastest response)
            import time
            start_time = time.time()
            
            try:
                process = self.program_sync.spawn_program(program_name)
                self.logger.info(f"[blue]►[/blue] [cyan]{program_name}[/cyan]")
                
                # Update status AFTER spawning (in background)
                asyncio.create_task(self._update_and_monitor(process, program_name, command_id, start_time))
                
            except Exception as e:
                # If spawn fails, record failure immediately
                self.logger.error(f"[red]✗ Failed to spawn:[/red] [cyan]{program_name}[/cyan] - {e}")
                
                self.supabase.table('script_results').insert({
                    'command_id': command_id,
                    'exit_code': 1,
                    'stdout': '',
                    'stderr': str(e),
                    'success': False,
                    'result': {"error": str(e)}
                }).execute()
                
                self.supabase.table('script_commands').update({
                    'status': 'failed'
                }).eq('id', command_id).execute()
            
        except Exception as e:
            self.logger.error(f"Execution failed for {command_id}: {e}")
            try:
                self.supabase.table('script_commands').update({
                    'status': 'failed'
                }).eq('id', command_id).execute()
            except:
                pass
    
    async def _update_and_monitor(self, process, program_name: str, command_id: str, start_time: float):
        """Update status and monitor a spawned process in the background"""
        try:
            # Update status to executing (after spawn)
            self.supabase.table('script_commands').update({
                'status': 'executing'
            }).eq('id', command_id).execute()
            # Wait for process to complete
            stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, process.communicate
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            success = process.returncode == 0
            final_status = 'completed' if success else 'failed'
            
            # Record result
            self.supabase.table('script_results').insert({
                'command_id': command_id,
                'exit_code': process.returncode,
                'stdout': stdout or '',
                'stderr': stderr or '',
                'success': success,
                'result': {
                    "duration_ms": duration_ms,
                    "returncode": process.returncode
                }
            }).execute()
            
            # Update command status
            self.supabase.table('script_commands').update({
                'status': final_status
            }).eq('id', command_id).execute()
            
            if success:
                self.logger.info(f"[green]✓[/green] [cyan]{program_name}[/cyan] [dim]({duration_ms}ms)[/dim]")
            else:
                self.logger.error(f"[red]✗[/red] [cyan]{program_name}[/cyan] [dim]({duration_ms}ms)[/dim]")
                
        except Exception as e:
            self.logger.error(f"Error monitoring {program_name}: {e}")
    
    def start_heartbeat(self):
        """Start heartbeat thread"""
        def heartbeat():
            while self.running:
                try:
                    current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    self.supabase.table('hubs').update({
                        'status': 'online',
                        'last_seen': current_time
                    }).eq('id', self.hub_id).execute()
                    
                    time.sleep(30)  # 30 second heartbeat
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")
                    time.sleep(30)
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        self.logger.info("[green]Heartbeat:[/green] [bright_green]Started[/bright_green]")
    
    async def run_async(self):
        """Main async run loop"""
        try:
            # Sync programs from GitHub
            if not await self.sync_programs():
                self.logger.error("Failed to sync programs")
                return
            
            # Register with Supabase
            if not self.register_hub():
                self.logger.error("Failed to register hub")
                return
            
            # Setup real-time and presence
            await self.setup_realtime_channel()
            await self.start_presence()
            
            # Start heartbeat
            self.start_heartbeat()
            
            # Show ready banner
            if not self.silent_mode:
                ready_panel = Panel.fit(
                    f"[bold green]ONLINE AND READY[/bold green]\n\n"
                    f"[bright_green]Programs:[/bright_green] [yellow]{len(self.available_programs)}[/yellow]\n"
                    f"[bright_green]Real-time:[/bright_green] [green]Connected[/green]\n"
                    f"[bright_green]Heartbeat:[/bright_green] [green]Running[/green]\n\n"
                    f"[dim]Waiting for commands...[/dim]",
                    title="[bold bright_green]SP CREW HUB READY[/bold bright_green]",
                    border_style="bright_green"
                )
                self.console.print(ready_panel)
            
            # Main loop
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.running = False
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup connections and set offline"""
        try:
            if self.channel:
                await self.channel.unsubscribe()
            if self.presence_channel:
                await self.presence_channel.unsubscribe()
                
            if self.hub_id:
                self.supabase.table('hubs').update({
                    'status': 'offline'
                }).eq('id', self.hub_id).execute()
                
            self.logger.info("Cleanup complete")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def run(self):
        """Run the hub"""
        asyncio.run(self.run_async())


def main():
    """Entry point"""
    silent_mode = "--silent" in sys.argv or "silent" in sys.argv[0].lower()
    
    hub = SPCrewHub(silent_mode=silent_mode)
    hub.run()


if __name__ == "__main__":
    main()