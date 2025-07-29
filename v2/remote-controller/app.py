#!/usr/bin/env python3
"""
SP Crew Control V2 - Remote Controller Service
Web interface that connects to Message Relay for hub coordination
"""

import json
import os
import sys
import time
import logging
import threading
import uuid
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from flask import Flask, render_template_string, jsonify, request, session
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
        
        # Message Relay configuration
        self.relay_base_url = "https://sp-script-holder-1912.vercel.app"
        
        # State management
        self.available_hubs = []
        self.current_session = None
        self.current_hub = None
        self.current_mode = "single_button"
        self.assigned_script = None
        self.all_scripts = []
        
        # Auto-refresh thread
        self.refresh_thread = None
        self.should_refresh = True
        
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
        """Discover available hubs through Message Relay"""
        try:
            response = requests.get(
                f"{self.relay_base_url}/api/discover-hubs",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.available_hubs = data.get('hubs', [])
                return self.available_hubs
            else:
                self.logger.error(f"Hub discovery failed: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Hub discovery error: {e}")
            return []

    def create_session(self, hub_id: str) -> Optional[str]:
        """Create a new session with a hub"""
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/join-session",
                json={
                    "action": "create",
                    "hub_id": hub_id,
                    "remote_id": self.remote_id,
                    "remote_name": self.remote_name
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    session_id = data.get('session_id')
                    self.current_session = session_id
                    self.current_hub = hub_id
                    self.logger.info(f"Created session {session_id} with hub {hub_id}")
                    return session_id
                    
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
            
        return None

    def join_session(self, session_id: str) -> bool:
        """Join an existing session"""
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/join-session",
                json={
                    "action": "join",
                    "session_id": session_id,
                    "remote_id": self.remote_id,
                    "remote_name": self.remote_name
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    session_data = data.get('session', {})
                    self.current_session = session_id
                    self.current_hub = session_data.get('hub_id')
                    self.current_mode = session_data.get('mode', 'single_button')
                    self.assigned_script = session_data.get('assignments', {}).get(self.remote_id)
                    self.all_scripts = session_data.get('all_scripts', [])
                    return True
                    
        except Exception as e:
            self.logger.error(f"Session join error: {e}")
            
        return False

    def execute_script(self, script_name: str) -> Dict[str, Any]:
        """Execute a script through the relay"""
        if not self.current_session:
            return {"success": False, "error": "No active session"}
            
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/broadcast",
                json={
                    "action": "execute_script",
                    "session_id": self.current_session,
                    "remote_id": self.remote_id,
                    "remote_name": self.remote_name,
                    "script_name": script_name
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"Execution failed: {response.text}"}
                
        except Exception as e:
            self.logger.error(f"Script execution error: {e}")
            return {"success": False, "error": str(e)}

    def change_mode(self, new_mode: str) -> bool:
        """Change mode for ALL remotes in session"""
        if not self.current_session:
            return False
            
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/join-session",
                json={
                    "action": "change_mode",
                    "session_id": self.current_session,
                    "mode": new_mode,
                    "remote_id": self.remote_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.current_mode = new_mode
                    return True
                    
        except Exception as e:
            self.logger.error(f"Mode change error: {e}")
            
        return False

    def shuffle_scripts(self) -> bool:
        """Shuffle script assignments for ALL remotes"""
        if not self.current_session or self.current_mode != "single_button":
            return False
            
        try:
            response = requests.post(
                f"{self.relay_base_url}/api/join-session",
                json={
                    "action": "shuffle",
                    "session_id": self.current_session,
                    "remote_id": self.remote_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Update our assigned script
                    assignments = data.get('assignments', {})
                    self.assigned_script = assignments.get(self.remote_id)
                    return True
                    
        except Exception as e:
            self.logger.error(f"Shuffle error: {e}")
            
        return False

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
                "current_session": self.current_session,
                "current_hub": self.current_hub,
                "current_mode": self.current_mode,
                "assigned_script": self.assigned_script,
                "available_hubs": len(self.available_hubs),
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
                
            session_id = self.create_session(hub_id)
            if session_id:
                return jsonify({"success": True, "session_id": session_id})
            else:
                return jsonify({"success": False, "error": "Failed to create session"}), 500
                
        @self.app.route('/api/execute-script', methods=['POST'])
        def api_execute_script():
            data = request.get_json()
            script_name = data.get('script_name')
            
            if not script_name:
                return jsonify({"success": False, "error": "script_name required"}), 400
                
            result = self.execute_script(script_name)
            return jsonify(result)
            
        @self.app.route('/api/change-mode', methods=['POST'])
        def api_change_mode():
            data = request.get_json()
            new_mode = data.get('mode')
            
            if new_mode not in ['single_button', 'all_buttons']:
                return jsonify({"success": False, "error": "Invalid mode"}), 400
                
            success = self.change_mode(new_mode)
            return jsonify({"success": success})
            
        @self.app.route('/api/shuffle', methods=['POST'])
        def api_shuffle():
            success = self.shuffle_scripts()
            return jsonify({"success": success})

    def start_refresh_thread(self):
        """Start background refresh thread for session updates"""
        def refresh_loop():
            while self.should_refresh:
                if self.current_session:
                    # Refresh session state periodically
                    self.join_session(self.current_session)
                time.sleep(5)  # Update every 5 seconds
                
        self.refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self.refresh_thread.start()
        self.logger.info("Session refresh thread started")

    def run(self, host='0.0.0.0', port=5001, debug=False):
        """Start the Remote Controller service"""
        self.logger.info(f"Starting Remote Controller on {host}:{port}")
        
        # Start refresh thread
        self.start_refresh_thread()
        
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
        .mode-switcher {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 20px;
        }
        .loading {
            text-align: center;
            color: #00cc33;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🛡️ CREW CONTROL</h1>
            <p class="subtitle">Remote Controller</p>
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
        
        <!-- Control Panel -->
        <div class="section" id="controlSection" style="display: none;">
            <h3>Control Panel</h3>
            
            <!-- Mode Switcher (affects ALL remotes) -->
            <div class="mode-switcher">
                <label>Mode (applies to ALL remotes):</label>
                <button class="btn" id="singleModeBtn" onclick="changeMode('single_button')">Single Button</button>
                <button class="btn" id="allModeBtn" onclick="changeMode('all_buttons')">All Buttons</button>
                <button class="btn" onclick="shuffleScripts()" id="shuffleBtn">🔀 Shuffle</button>
            </div>
            
            <!-- Single Button Mode -->
            <div id="singleButtonMode">
                <h4>Your Assigned Script:</h4>
                <div id="assignedScript" class="script-grid"></div>
            </div>
            
            <!-- All Buttons Mode -->
            <div id="allButtonsMode" style="display: none;">
                <h4>All Available Scripts:</h4>
                <div id="allScripts" class="script-grid"></div>
            </div>
        </div>
    </div>
    
    <script>
        let currentSession = null;
        let currentMode = 'single_button';
        let updateInterval = null;
        
        // Auto-refresh status
        function startStatusUpdates() {
            updateInterval = setInterval(updateStatus, 2000);
        }
        
        function stopStatusUpdates() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                currentSession = data.current_session;
                currentMode = data.current_mode;
                
                // Update connection status
                const statusIndicator = document.querySelector('.status-indicator');
                const statusText = document.getElementById('statusText');
                
                if (currentSession) {
                    statusIndicator.className = 'status-indicator status-online';
                    statusText.textContent = `Connected to session ${currentSession}`;
                    document.getElementById('hubSection').style.display = 'none';
                    document.getElementById('controlSection').style.display = 'block';
                    
                    // Update mode buttons
                    updateModeButtons();
                    
                    // Update script display based on mode
                    if (currentMode === 'single_button') {
                        document.getElementById('singleButtonMode').style.display = 'block';
                        document.getElementById('allButtonsMode').style.display = 'none';
                        updateAssignedScript(data.assigned_script);
                    } else {
                        document.getElementById('singleButtonMode').style.display = 'none';
                        document.getElementById('allButtonsMode').style.display = 'block';
                        updateAllScripts();
                    }
                } else {
                    statusIndicator.className = 'status-indicator status-offline';
                    statusText.textContent = 'Disconnected';
                    document.getElementById('hubSection').style.display = 'block';
                    document.getElementById('controlSection').style.display = 'none';
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        function updateModeButtons() {
            const singleBtn = document.getElementById('singleModeBtn');
            const allBtn = document.getElementById('allModeBtn');
            const shuffleBtn = document.getElementById('shuffleBtn');
            
            if (currentMode === 'single_button') {
                singleBtn.classList.add('btn-primary');
                allBtn.classList.remove('btn-primary');
                shuffleBtn.disabled = false;
            } else {
                singleBtn.classList.remove('btn-primary');
                allBtn.classList.add('btn-primary');
                shuffleBtn.disabled = true;
            }
        }
        
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
                        <div><strong>${hub.hub_name}</strong></div>
                        <div>Location: ${hub.hub_location || 'Unknown'}</div>
                        <div>Scripts: ${hub.script_count}</div>
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
                    currentSession = data.session_id;
                    updateStatus();
                } else {
                    alert('Failed to connect to hub: ' + data.error);
                }
            } catch (error) {
                console.error('Hub connection error:', error);
                alert('Connection error: ' + error.message);
            }
        }
        
        async function changeMode(newMode) {
            try {
                const response = await fetch('/api/change-mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: newMode })
                });
                
                const data = await response.json();
                if (data.success) {
                    currentMode = newMode;
                    updateStatus();
                } else {
                    alert('Failed to change mode');
                }
            } catch (error) {
                console.error('Mode change error:', error);
            }
        }
        
        async function shuffleScripts() {
            try {
                const response = await fetch('/api/shuffle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                if (data.success) {
                    updateStatus();
                } else {
                    alert('Failed to shuffle scripts');
                }
            } catch (error) {
                console.error('Shuffle error:', error);
            }
        }
        
        async function executeScript(scriptName) {
            try {
                const response = await fetch('/api/execute-script', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ script_name: scriptName })
                });
                
                const data = await response.json();
                if (!data.success) {
                    alert('Script execution failed: ' + data.error);
                }
            } catch (error) {
                console.error('Script execution error:', error);
                alert('Execution error: ' + error.message);
            }
        }
        
        function updateAssignedScript(script) {
            const container = document.getElementById('assignedScript');
            if (script) {
                container.innerHTML = `
                    <button class="btn script-btn btn-primary" onclick="executeScript('${script.name}')">
                        ${script.display_name || script.name}
                    </button>
                `;
            } else {
                container.innerHTML = '<div class="loading">No script assigned</div>';
            }
        }
        
        function updateAllScripts() {
            // This would be populated from session data
            const container = document.getElementById('allScripts');
            container.innerHTML = '<div class="loading">Loading all scripts...</div>';
        }
        
        // Initialize
        updateStatus();
        startStatusUpdates();
        discoverHubs();
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