#!/usr/bin/env python3
"""
SP Crew Control V2 - Hub Worker Service
Pure script execution engine that registers with Message Relay
"""

import json
import os
import sys
import time
import logging
import threading
import subprocess
import platform
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
import websocket
from flask import Flask, render_template_string, jsonify

# Add project root to path for script imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class HubWorker:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_flask_routes()
        self.setup_logging()
        
        # Hub configuration
        self.hub_id = self.generate_hub_id()
        self.hub_name = f"Hub-{socket.gethostname()}"
        self.hub_location = self.detect_location()
        
        # Message Relay configuration
        self.relay_base_url = "https://sp-crew-control-relay.vercel.app"
        self.websocket_url = f"ws://localhost:8765/{self.hub_id}"
        
        # Script management
        self.scripts_dir = project_root / "scripts"
        self.available_scripts = self.scan_available_scripts()
        
        # WebSocket server
        self.ws_server = None
        self.connected_clients = set()
        
        # Status tracking
        self.last_heartbeat = None
        self.registration_status = False
        
        self.logger.info(f"Hub Worker initialized: {self.hub_id} ({self.hub_name})")

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

    def detect_location(self) -> str:
        """Detect hub location based on system info"""
        try:
            # Try to get location from environment or config
            location = os.environ.get('HUB_LOCATION')
            if location:
                return location
                
            # Fallback to hostname-based detection
            hostname = socket.gethostname().lower()
            if 'arkansas' in hostname or 'ar-' in hostname:
                return "Arkansas Hub"
            elif 'jersey' in hostname or 'nj-' in hostname:
                return "New Jersey Hub"
            else:
                return f"{socket.gethostname()} Hub"
        except Exception:
            return "Unknown Location"

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
                "type": "python",
                "description": self.extract_script_description(script_file)
            }
            scripts.append(script_info)
            
        # Scan for PowerShell scripts
        for script_file in self.scripts_dir.glob("*.ps1"):
            script_info = {
                "name": script_file.stem,
                "display_name": script_file.stem.replace('_', ' ').title(),
                "file_path": str(script_file),
                "type": "powershell",
                "description": self.extract_script_description(script_file)
            }
            scripts.append(script_info)
            
        self.logger.info(f"Found {len(scripts)} available scripts")
        return scripts

    def extract_script_description(self, script_file: Path) -> str:
        """Extract description from script file docstring or comments"""
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read(500)  # Read first 500 chars
                
            if script_file.suffix == '.py':
                # Look for docstring
                if '"""' in content:
                    start = content.find('"""') + 3
                    end = content.find('"""', start)
                    if end > start:
                        return content[start:end].strip()
                        
            elif script_file.suffix == '.ps1':
                # Look for PowerShell comments
                lines = content.split('\n')[:5]
                for line in lines:
                    line = line.strip()
                    if line.startswith('#') and len(line) > 2:
                        return line[1:].strip()
                        
            return f"Script: {script_file.name}"
        except Exception:
            return f"Script: {script_file.name}"

    def register_with_relay(self) -> bool:
        """Register this hub with the Message Relay"""
        registration_data = {
            "hub_id": self.hub_id,
            "hub_name": self.hub_name,
            "hub_location": self.hub_location,
            "scripts": self.available_scripts,
            "websocket_url": self.websocket_url,
            "max_remotes": 6,
            "latency_ms": 0  # Will be calculated during heartbeat
        }
        
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/discover-hubs",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.registration_status = True
                self.logger.info(f"Successfully registered with Message Relay")
                return True
            else:
                self.logger.error(f"Registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False

    def send_heartbeat(self) -> bool:
        """Send heartbeat to Message Relay"""
        try:
            start_time = time.time()
            response = requests.put(
                f"{self.relay_base_url}/api/discover-hubs",
                params={"hubId": self.hub_id},
                timeout=5
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                self.last_heartbeat = datetime.now()
                self.logger.debug(f"Heartbeat sent (latency: {latency_ms}ms)")
                return True
            else:
                self.logger.warning(f"Heartbeat failed: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Heartbeat error: {e}")
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
                # Execute Python script
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=script_path.parent
                )
            elif script_info["type"] == "powershell":
                # Execute PowerShell script
                result = subprocess.run(
                    ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=script_path.parent
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported script type: {script_info['type']}",
                    "duration_ms": 0
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                self.logger.info(f"Script '{script_name}' executed successfully in {duration_ms}ms")
                return {
                    "success": True,
                    "output": result.stdout,
                    "duration_ms": duration_ms
                }
            else:
                self.logger.error(f"Script '{script_name}' failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "duration_ms": duration_ms
                }
                
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

    def setup_flask_routes(self):
        """Setup Flask web interface routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_TEMPLATE, 
                hub_id=getattr(self, 'hub_id', 'Initializing...'),
                hub_name=getattr(self, 'hub_name', 'Loading...'),
                hub_location=getattr(self, 'hub_location', 'Unknown'),
                script_count=len(getattr(self, 'available_scripts', [])),
                registration_status=getattr(self, 'registration_status', False),
                last_heartbeat=getattr(self, 'last_heartbeat', None)
            )
            
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                "service": "SP Crew Control V2 Hub Worker",
                "hub_id": self.hub_id,
                "hub_name": self.hub_name,
                "hub_location": self.hub_location,
                "status": "online",
                "registration_status": self.registration_status,
                "available_scripts": len(self.available_scripts),
                "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                "websocket_url": self.websocket_url,
                "timestamp": datetime.now().isoformat()
            })
            
        @self.app.route('/api/scripts')
        def api_scripts():
            return jsonify({
                "success": True,
                "scripts": self.available_scripts,
                "count": len(self.available_scripts)
            })

    def start_heartbeat_thread(self):
        """Start background heartbeat thread"""
        def heartbeat_loop():
            while True:
                if self.registration_status:
                    if not self.send_heartbeat():
                        # Re-register if heartbeat fails
                        self.logger.warning("Heartbeat failed, attempting re-registration")
                        self.register_with_relay()
                else:
                    # Try to register if not registered
                    self.register_with_relay()
                    
                time.sleep(30)  # Heartbeat every 30 seconds
                
        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
        self.logger.info("Heartbeat thread started")

    def run(self, host='0.0.0.0', port=5002, debug=False):
        """Start the Hub Worker service"""
        self.logger.info(f"Starting Hub Worker on {host}:{port}")
        
        # Initial registration
        self.register_with_relay()
        
        # Start heartbeat thread
        self.start_heartbeat_thread()
        
        # Start Flask web interface
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)

# Dashboard template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ hub_name }} - Crew Control Hub Worker</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
            color: #00ff41;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff41;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid #00ff41;
            padding-bottom: 20px;
        }
        .title {
            font-size: 2.5em;
            text-shadow: 0 0 10px #00ff41;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #00cc33;
            font-size: 1.2em;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(0, 20, 0, 0.6);
            border: 1px solid #00ff41;
            border-radius: 5px;
            padding: 20px;
        }
        .status-card h3 {
            color: #00ff41;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        .status-value {
            font-size: 1.1em;
            color: #ffffff;
            margin-bottom: 5px;
        }
        .status-online { color: #00ff41; }
        .status-offline { color: #ff4400; }
        .info-section {
            background: rgba(0, 20, 0, 0.6);
            border: 1px solid #00ff41;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
        .refresh-btn {
            background: transparent;
            border: 2px solid #00ff41;
            color: #00ff41;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-size: 1em;
            transition: all 0.3s;
        }
        .refresh-btn:hover {
            background: #00ff41;
            color: #000000;
            box-shadow: 0 0 15px #00ff41;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🛡️ CREW CONTROL</h1>
            <p class="subtitle">Hub Worker Service - Monitoring Only</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>Hub Information</h3>
                <div class="status-value">ID: {{ hub_id }}</div>
                <div class="status-value">Name: {{ hub_name }}</div>
                <div class="status-value">Location: {{ hub_location }}</div>
            </div>
            
            <div class="status-card">
                <h3>Service Status</h3>
                <div class="status-value status-{% if registration_status %}online{% else %}offline{% endif %}">
                    Registration: {% if registration_status %}Connected{% else %}Disconnected{% endif %}
                </div>
                <div class="status-value">Scripts Available: {{ script_count }}</div>
                <div class="status-value">
                    Last Heartbeat: {% if last_heartbeat %}{{ last_heartbeat.strftime('%H:%M:%S') }}{% else %}Never{% endif %}
                </div>
            </div>
        </div>
        
        <div class="info-section">
            <h3>About This Hub Worker</h3>
            <p>This is a monitoring-only interface for the Hub Worker service. The hub automatically:</p>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li>Registers with the Message Relay service</li>
                <li>Sends regular heartbeats to maintain connection</li>
                <li>Executes scripts when requested by Remote Controllers</li>
                <li>Reports execution results back to the relay</li>
            </ul>
            <br>
            <p><strong>Note:</strong> Remote control is handled through the Message Relay system. This hub cannot be controlled directly from this interface.</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="refresh-btn" onclick="location.reload()">Refresh Status</button>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SP Crew Control V2 Hub Worker")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5002, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    hub = HubWorker()
    hub.run(host=args.host, port=args.port, debug=args.debug)