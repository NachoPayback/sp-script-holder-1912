#!/usr/bin/env python3
"""
SP Crew Control V2 - Hub Worker Service (Headless)
Pure script execution engine using Supabase real-time messaging
No web UI - just executes scripts when commanded
"""

import json
import os
import sys
import time
import logging
import threading
import subprocess
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from supabase import create_client, Client

# Add project root to path for script imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class HubWorker:
    def __init__(self):
        self.setup_logging()
        
        # Hub configuration
        self.hub_id = self.generate_hub_id()
        self.hub_name = f"Hub-{socket.gethostname()}"
        
        # Supabase configuration
        self.supabase_url = "https://qcefzjjxnwccjivsbtgb.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIskmV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Script management
        self.scripts_dir = project_root / "legacy" / "scripts"
        self.available_scripts = self.scan_available_scripts()
        
        # Real-time messaging
        self.channel = None
        
        # Status tracking
        self.running = True
        
        self.logger.info(f"Hub Worker initialized: {self.hub_id} ({self.hub_name})")
        self.logger.info(f"Found {len(self.available_scripts)} scripts")

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"hub_worker_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('HubWorker')

    def generate_hub_id(self) -> str:
        """Generate unique hub ID based on hostname and UUID"""
        hostname = socket.gethostname().lower().replace(' ', '-')
        unique_suffix = str(uuid.uuid4())[:8]
        return f"hub-{hostname}-{unique_suffix}"

    def scan_available_scripts(self) -> List[Dict[str, Any]]:
        """Scan scripts directory for available scripts"""
        scripts = []
        
        if not self.scripts_dir.exists():
            self.logger.warning(f"Scripts directory not found: {self.scripts_dir}")
            return scripts
            
        # Scan for Python scripts
        for script_file in self.scripts_dir.glob("*.py"):
            if script_file.name.startswith('__'):
                continue
                
            script_info = {
                "name": script_file.stem,
                "display_name": script_file.stem.replace('_', ' ').title(),
                "file_path": str(script_file),
                "type": "python"
            }
            scripts.append(script_info)
            
        # Scan for PowerShell scripts
        for script_file in self.scripts_dir.glob("*.ps1"):
            script_info = {
                "name": script_file.stem,
                "display_name": script_file.stem.replace('_', ' ').title(),
                "file_path": str(script_file),
                "type": "powershell"
            }
            scripts.append(script_info)
            
        return scripts

    def register_hub(self):
        """Register this hub in Supabase"""
        try:
            hub_data = {
                "hub_id": self.hub_id,
                "hub_name": self.hub_name,
                "status": "online",
                "scripts": self.available_scripts,
                "last_heartbeat": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            self.supabase.table("hubs").upsert(hub_data, on_conflict="hub_id").execute()
            self.logger.info(f"Hub registered with Supabase: {self.hub_id}")
            return True
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False

    def execute_script(self, script_name: str, remote_id: str) -> Dict[str, Any]:
        """Execute a script and return results"""
        start_time = time.time()
        
        # Find script info
        script_info = None
        for script in self.available_scripts:
            if script["name"] == script_name:
                script_info = script
                break
                
        if not script_info:
            return {
                "success": False,
                "error": f"Script not found: {script_name}",
                "duration_ms": 0
            }
            
        self.logger.info(f"Executing script '{script_name}' for remote '{remote_id}'")
        
        try:
            script_path = Path(script_info["file_path"])
            
            if script_info["type"] == "python":
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=script_path.parent
                )
            elif script_info["type"] == "powershell":
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=script_path.parent
                )
            else:
                return {"success": False, "error": f"Unsupported script type: {script_info['type']}", "duration_ms": 0}
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout if result.returncode == 0 else result.stderr,
                "duration_ms": duration_ms,
                "script_name": script_name,
                "timestamp": datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                self.logger.info(f"Script '{script_name}' executed successfully in {duration_ms}ms")
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
            data = payload.get('new', {})
            script_name = data.get('script_name')
            remote_id = data.get('remote_id')
            message_id = data.get('id')
            
            if not script_name or not remote_id:
                self.logger.error(f"Invalid execute message: {data}")
                return
                
            # Execute the script
            result = self.execute_script(script_name, remote_id)
            
            # Send result back through database
            response_data = {
                "message_id": message_id,
                "type": "script_result",
                "result": result
            }
            
            self.supabase.table("script_results").insert(response_data).execute()
            self.logger.info(f"Result sent for script '{script_name}' (ID: {message_id})")
            
        except Exception as e:
            self.logger.error(f"Error handling execute message: {e}")

    def setup_realtime_channel(self):
        """Setup Supabase real-time channel for listening to commands"""
        try:
            self.channel = self.supabase.channel(f"hub-{self.hub_id}")
            
            # Listen for new script execution commands
            self.channel.on("INSERT", "script_commands", self.handle_execute_message)
            
            # Subscribe to the channel
            self.channel.subscribe()
            
            self.logger.info(f"Subscribed to real-time channel")
            
        except Exception as e:
            self.logger.error(f"Error setting up real-time channel: {e}")

    def start_heartbeat_thread(self):
        """Start background heartbeat thread"""
        def heartbeat_loop():
            while self.running:
                try:
                    self.supabase.table("hubs").update({
                        "last_heartbeat": datetime.now().isoformat(),
                        "status": "online"
                    }).eq("hub_id", self.hub_id).execute()
                    
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")
                    
                time.sleep(30)  # Heartbeat every 30 seconds
                
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
        self.logger.info("Heartbeat thread started")

    def run(self):
        """Start the Hub Worker service (headless)"""
        self.logger.info("Starting Hub Worker (headless mode)")
        
        # Register with Supabase
        if not self.register_hub():
            self.logger.error("Failed to register hub. Exiting.")
            return
        
        # Setup real-time messaging
        self.setup_realtime_channel()
        
        # Start heartbeat thread
        self.start_heartbeat_thread()
        
        self.logger.info("Hub Worker is running. Press Ctrl+C to stop.")
        
        try:
            # Keep running until interrupted
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down Hub Worker...")
            self.running = False
            
            # Update status to offline
            try:
                self.supabase.table("hubs").update({
                    "status": "offline"
                }).eq("hub_id", self.hub_id).execute()
            except:
                pass

if __name__ == "__main__":
    hub = HubWorker()
    hub.run()