#!/usr/bin/env python3
"""
SP Crew Control V2 - Remote Controller Service
Web interface using Supabase real-time messaging for instant button execution
"""

import json
import os
import sys
import time
import logging
import threading
import socket
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from supabase import create_client, Client
from flask import Flask, render_template_string, jsonify, request
from werkzeug.serving import WSGIRequestHandler

class RemoteController:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        self.setup_flask_routes()
        self.setup_logging()
        
        # Remote configuration
        self.remote_id = self.generate_remote_id() 
        self.remote_name = f"Remote-{socket.gethostname()}"
        
        # Supabase configuration
        self.supabase_url = "https://qcefzjjxnwccjivsbtgb.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4"
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # State management
        self.available_hubs = []
        self.current_hub = None
        self.hub_scripts = []
        self.execution_results = {}
        
        # Real-time channel
        self.channel = None
        
        self.logger.info(f"Remote Controller initialized: {self.remote_id} ({self.remote_name})")

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"remote_controller_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('RemoteController')

    def generate_remote_id(self) -> str:
        """Generate unique remote ID"""
        hostname = socket.gethostname().lower().replace(' ', '-')
        unique_suffix = str(uuid.uuid4())[:8] 
        return f"remote-{hostname}-{unique_suffix}"

    def discover_hubs(self) -> List[Dict[str, Any]]:
        """Discover available hubs from Supabase"""
        try:
            # Get hubs that have sent heartbeat in last 2 minutes
            cutoff_time = datetime.now().isoformat()
            
            response = self.supabase.table("hubs").select("*").gte("last_heartbeat", cutoff_time[:-10] + "00:00:00").execute()
            
            self.available_hubs = []
            for hub in response.data:
                hub_info = {
                    "hub_id": hub["hub_id"],
                    "hub_name": hub["hub_name"], 
                    "status": hub["status"],
                    "script_count": len(hub.get("scripts", [])),
                    "scripts": hub.get("scripts", []),
                    "last_heartbeat": hub["last_heartbeat"]
                }
                self.available_hubs.append(hub_info)
                
            self.logger.info(f"Discovered {len(self.available_hubs)} active hubs")
            return self.available_hubs
            
        except Exception as e:
            self.logger.error(f"Hub discovery error: {e}")
            return []

    def connect_to_hub(self, hub_id: str) -> bool:
        """Connect to a specific hub"""
        try:
            # Find hub info
            hub_info = None
            for hub in self.available_hubs:
                if hub["hub_id"] == hub_id:
                    hub_info = hub
                    break
                    
            if not hub_info:
                self.logger.error(f"Hub not found: {hub_id}")
                return False
                
            self.current_hub = hub_info
            self.hub_scripts = hub_info.get("scripts", [])
            
            # Setup real-time channel for results
            self.setup_realtime_channel()
            
            self.logger.info(f"Connected to hub: {hub_id} ({hub_info['hub_name']})")
            return True
            
        except Exception as e:
            self.logger.error(f"Hub connection error: {e}")
            return False

    def execute_script(self, script_name: str) -> Dict[str, Any]:
        """Execute a script on the connected hub"""
        if not self.current_hub:
            return {"success": False, "error": "No hub connected"}
            
        try:
            # Insert command into script_commands table
            command_data = {
                "hub_id": self.current_hub["hub_id"],
                "remote_id": self.remote_id,
                "script_name": script_name,
                "created_at": datetime.now().isoformat()
            }
            
            response = self.supabase.table("script_commands").insert(command_data).execute()
            
            if response.data:
                command_id = response.data[0]["id"]
                self.logger.info(f"Script execution requested: {script_name} (ID: {command_id})")
                
                # Wait for result (with timeout)
                result = self.wait_for_result(command_id, timeout=35)
                return result
            else:
                return {"success": False, "error": "Failed to send command"}
                
        except Exception as e:
            self.logger.error(f"Script execution error: {e}")
            return {"success": False, "error": str(e)}

    def wait_for_result(self, command_id: int, timeout: int = 35) -> Dict[str, Any]:
        """Wait for script execution result"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check for result in script_results table
                response = self.supabase.table("script_results").select("*").eq("message_id", command_id).execute()
                
                if response.data:
                    result_data = response.data[0]
                    result = result_data.get("result", {})
                    self.logger.info(f"Received result for command {command_id}")
                    return result
                    
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Error waiting for result: {e}")
                break
                
        return {"success": False, "error": "Execution timeout"}

    def handle_script_result(self, payload):
        """Handle script execution results from real-time channel"""
        try:
            data = payload.get('new', {})
            message_id = data.get('message_id')
            result = data.get('result', {})
            
            if message_id:
                self.execution_results[message_id] = result
                self.logger.info(f"Received real-time result for message {message_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling script result: {e}")

    def setup_realtime_channel(self):
        """Setup Supabase real-time channel for receiving results"""
        try:
            # Subscribe to script_results table for this remote
            self.channel = self.supabase.channel(f"remote-{self.remote_id}")
            
            # Listen for new script results
            self.channel.on("INSERT", "script_results", self.handle_script_result)
            
            # Subscribe to the channel
            self.channel.subscribe()
            
            self.logger.info(f"Subscribed to real-time channel: remote-{self.remote_id}")
            
        except Exception as e:
            self.logger.error(f"Error setting up real-time channel: {e}")

    def setup_flask_routes(self):
        """Setup Flask web interface routes"""
        
        @self.app.route('/')
        def dashboard():
            return render_template_string(DASHBOARD_TEMPLATE)
            
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                "service": "SP Crew Control V2 Remote Controller",
                "remote_id": self.remote_id,
                "remote_name": self.remote_name,
                "current_hub": self.current_hub["hub_id"] if self.current_hub else None,
                "available_hubs": len(self.available_hubs),
                "hub_scripts": len(self.hub_scripts),
                "messaging": "Supabase Real-time",
                "timestamp": datetime.now().isoformat()
            })
            
        @self.app.route('/api/discover-hubs')
        def api_discover_hubs():
            hubs = self.discover_hubs()
            return jsonify({
                "success": True,
                "hubs": hubs,
                "count": len(hubs)
            })
            
        @self.app.route('/api/connect-hub', methods=['POST'])
        def api_connect_hub():
            data = request.get_json()
            hub_id = data.get('hub_id')
            
            if not hub_id:
                return jsonify({"success": False, "error": "hub_id required"}), 400
                
            success = self.connect_to_hub(hub_id)
            if success:
                return jsonify({
                    "success": True, 
                    "hub_id": hub_id,
                    "scripts": self.hub_scripts
                })
            else:
                return jsonify({"success": False, "error": "Failed to connect to hub"}), 500
                
        @self.app.route('/api/execute-script', methods=['POST'])
        def api_execute_script():
            data = request.get_json()
            script_name = data.get('script_name')
            
            if not script_name:
                return jsonify({"success": False, "error": "script_name required"}), 400
                
            result = self.execute_script(script_name)
            return jsonify(result)
            
        @self.app.route('/api/scripts')
        def api_scripts():
            return jsonify({
                "success": True,
                "scripts": self.hub_scripts,
                "count": len(self.hub_scripts),
                "hub": self.current_hub["hub_id"] if self.current_hub else None
            })

    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Start the Remote Controller service"""
        self.logger.info(f"Starting Remote Controller on {host}:{port}")
        
        # Quiet Flask logging for production
        if not debug:
            WSGIRequestHandler.log_request = lambda self, *args: None
            
        # Start Flask app
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)

# Dashboard template with cyberpunk theme
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Crew Control Remote</title>
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
        .section {
            background: rgba(0, 20, 0, 0.6);
            border: 1px solid #00ff41;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h3 {
            color: #00ff41;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .btn {
            background: transparent;
            border: 2px solid #00ff41;
            color: #00ff41;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-family: inherit;
            font-size: 1em;
            margin: 5px;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #00ff41;
            color: #000000;
            box-shadow: 0 0 15px #00ff41;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-primary {
            background: #00ff41;
            color: #000000;
        }
        .btn-primary:hover {
            background: #00cc33;
            box-shadow: 0 0 20px #00ff41;
        }
        .script-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .script-btn {
            padding: 20px;
            font-size: 1.1em;
            text-align: center;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background: #00ff41; }
        .status-offline { background: #ff4400; }
        .hub-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .hub-item {
            background: rgba(0, 40, 0, 0.4);
            border: 1px solid #00cc33;
            border-radius: 3px;
            padding: 15px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .hub-item:hover {
            background: rgba(0, 60, 0, 0.6);
            border-color: #00ff41;
        }
        .loading {
            text-align: center;
            color: #00cc33;
            font-style: italic;
        }
        .result-display {
            background: rgba(0, 0, 0, 0.8);
            border: 1px solid #00ff41;
            border-radius: 3px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 200px;
            overflow-y: auto;
        }
        .result-success { border-color: #00ff41; }
        .result-error { border-color: #ff4400; color: #ff4400; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🛡️ CREW CONTROL</h1>
            <p class="subtitle">Remote Controller - Real-time</p>
        </div>
        
        <!-- Connection Status -->
        <div class="section">
            <h3>Connection Status</h3>
            <div id="connectionStatus">
                <span class="status-indicator status-offline"></span>
                <span id="statusText">Disconnected</span>
            </div>
        </div>
        
        <!-- Hub Discovery -->
        <div class="section" id="hubSection">
            <h3>Available Hubs</h3>
            <button class="btn" onclick="discoverHubs()">🔍 Discover Hubs</button>
            <div id="hubList" class="hub-list"></div>
        </div>
        
        <!-- Script Control -->
        <div class="section" id="scriptSection" style="display: none;">
            <h3>Available Scripts</h3>
            <div id="scriptGrid" class="script-grid"></div>
            <div id="executionResult" class="result-display" style="display: none;"></div>
        </div>
    </div>
    
    <script>
        let currentHub = null;
        let scripts = [];
        
        async function discoverHubs() {
            try {
                const response = await fetch('/api/discover-hubs');
                const data = await response.json();
                
                const hubList = document.getElementById('hubList');
                hubList.innerHTML = '';
                
                if (data.hubs.length === 0) {
                    hubList.innerHTML = '<div class="loading">No hubs found. Make sure Hub Workers are running.</div>';
                    return;
                }
                
                data.hubs.forEach(hub => {
                    const hubItem = document.createElement('div');
                    hubItem.className = 'hub-item';
                    hubItem.innerHTML = `
                        <div><strong>${hub.hub_name}</strong> (${hub.hub_id})</div>
                        <div>Status: ${hub.status}</div>
                        <div>Scripts: ${hub.script_count}</div>
                        <div>Last seen: ${new Date(hub.last_heartbeat).toLocaleTimeString()}</div>
                    `;
                    hubItem.onclick = () => connectToHub(hub.hub_id);
                    hubList.appendChild(hubItem);
                });
            } catch (error) {
                console.error('Hub discovery error:', error);
            }
        }
        
        async function connectToHub(hubId) {
            try {
                const response = await fetch('/api/connect-hub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hub_id: hubId })
                });
                
                const data = await response.json();
                if (data.success) {
                    currentHub = hubId;
                    scripts = data.scripts;
                    updateUI();
                    showScripts();
                } else {
                    alert('Failed to connect to hub: ' + data.error);
                }
            } catch (error) {
                console.error('Hub connection error:', error);
                alert('Connection error: ' + error.message);
            }
        }
        
        function updateUI() {
            const statusIndicator = document.querySelector('.status-indicator');
            const statusText = document.getElementById('statusText');
            
            if (currentHub) {
                statusIndicator.className = 'status-indicator status-online';
                statusText.textContent = `Connected to ${currentHub}`;
                document.getElementById('hubSection').style.display = 'none';
                document.getElementById('scriptSection').style.display = 'block';
            } else {
                statusIndicator.className = 'status-indicator status-offline';
                statusText.textContent = 'Disconnected';
                document.getElementById('hubSection').style.display = 'block';
                document.getElementById('scriptSection').style.display = 'none';
            }
        }
        
        function showScripts() {
            const grid = document.getElementById('scriptGrid');
            grid.innerHTML = '';
            
            if (scripts.length === 0) {
                grid.innerHTML = '<div class="loading">No scripts available on this hub</div>';
                return;
            }
            
            scripts.forEach(script => {
                const button = document.createElement('button');
                button.className = 'btn script-btn';
                button.textContent = script.display_name || script.name;
                button.onclick = () => executeScript(script.name);
                grid.appendChild(button);
            });
        }
        
        async function executeScript(scriptName) {
            const resultDiv = document.getElementById('executionResult');
            resultDiv.style.display = 'block';
            resultDiv.className = 'result-display';
            resultDiv.innerHTML = 'Executing ' + scriptName + '...';
            
            try {
                const response = await fetch('/api/execute-script', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ script_name: scriptName })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.className = 'result-display result-success';
                    resultDiv.innerHTML = `
                        <strong>✅ Success</strong><br>
                        Duration: ${result.duration_ms}ms<br>
                        Output: ${result.output || 'No output'}
                    `;
                } else {
                    resultDiv.className = 'result-display result-error';
                    resultDiv.innerHTML = `
                        <strong>❌ Error</strong><br>
                        ${result.error}
                    `;
                }
            } catch (error) {
                resultDiv.className = 'result-display result-error';
                resultDiv.innerHTML = `<strong>❌ Connection Error</strong><br>${error.message}`;
            }
        }
        
        // Initialize
        updateUI();
        discoverHubs();
        
        // Auto-refresh hub list every 30 seconds
        setInterval(discoverHubs, 30000);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SP Crew Control V2 Remote Controller")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    remote = RemoteController()
    remote.run(host=args.host, port=args.port, debug=args.debug)