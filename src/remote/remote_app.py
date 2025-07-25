#!/usr/bin/env python3
"""
P_Buttons Remote - Optimized version with consolidated patterns
"""

import asyncio
import json
import os
import uuid
import threading
import time
import secrets
import webbrowser
from datetime import datetime
from typing import Optional, Tuple

import nats
from flask import Flask, render_template, request, jsonify

# =============================================================================
# FLASK APP SETUP
# =============================================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

CONFIG_FILE = 'config/remote_config.json'

class OptimizedRemote:
    def __init__(self):
        # Change to project root directory
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        # Core state
        self.remote_id = self._load_or_generate_id()
        self.username = ''
        self.is_paired = False
        self.hub_token = ''
        self.assigned_command = ''  # Dynamic - never stored locally
        self.is_connected = False
        self.is_button_pressed = False
        
        # NATS connection
        self.nats_client = None
        self.nats_loop = None
        self.nats_config = self._load_nats_config()
        
        # Runtime state tracking
        self.assignment_updated = False
        self.shuffle_state = None
        self.timer_enabled = False
        self.timer_minutes = 10
        self.available_scripts = []
        self.hub_remote_list = []
        self.all_remotes = {}
        
        # Initialize
        self.load_config()
        self.setup_nats()

    # =============================================================================
    # UNIFIED CONFIG & PERSISTENCE
    # =============================================================================
    
    def _load_json(self, file_path, default=None):
        """Unified JSON loading with error handling"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Could not load {file_path}: {e}")
        return default or {}

    def _save_json(self, file_path, data):
        """Unified JSON saving with error handling"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving {file_path}: {e}")

    def _load_or_generate_id(self):
        """Load existing remote ID or generate new one"""
        config = self._load_json(CONFIG_FILE)
        return config.get('remote_id', f"Remote-{uuid.uuid4().hex[:8].upper()}")

    def _load_nats_config(self):
        """Load NATS configuration from hub config"""
        try:
            hub_config_path = 'config/config.json'
            config = self._load_json(hub_config_path)
            if config:
                return {
                    'nats_url': config.get('nats_url', 'nats://demo.nats.io:4222'),
                    'subject_prefix': config.get('subject_prefix', 'automation')
                }
        except Exception as e:
            print(f"Error loading NATS config: {e}")
        
        return {
            'nats_url': 'nats://demo.nats.io:4222',
            'subject_prefix': 'automation'
        }

    def load_config(self):
        """Load configuration from file"""
        config = self._load_json(CONFIG_FILE)
        if config:
            self.hub_token = config.get('hub_token', '')
            self.is_paired = bool(self.hub_token)
            self.username = config.get('username', '')

    def save_config(self):
        """Save configuration to file"""
        config = {
            'remote_id': self.remote_id,
            'username': self.username,
            'hub_token': self.hub_token,
            'last_updated': datetime.now().isoformat()
        }
        self._save_json(CONFIG_FILE, config)

    # =============================================================================
    # NATS CONNECTION & MESSAGING
    # =============================================================================
    
    def setup_nats(self):
        """Setup NATS connection in background thread"""
        try:
            threading.Thread(target=self._connect_nats, daemon=True).start()
        except Exception as e:
            print(f"Error setting up NATS: {e}")

    def _connect_nats(self):
        """Connect to NATS server and handle messages"""
        try:
            self.nats_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.nats_loop)
            self.nats_loop.run_until_complete(self._nats_connect_and_run())
        except Exception as e:
            print(f"Error connecting to NATS: {e}")

    async def _nats_connect_and_run(self):
        """Main NATS connection logic"""
        self.nats_client = await nats.connect(self.nats_config['nats_url'])
        print(f"Connected to NATS as {self.remote_id}")
        self.is_connected = True
        
        # Subscribe to messages
        await self.nats_client.subscribe(f"{self.nats_config['subject_prefix']}.response.{self.remote_id}", cb=self.handle_response)
        await self.nats_client.subscribe(f"{self.nats_config['subject_prefix']}.broadcast", cb=self.handle_broadcast)
        
        # Auto-discover and connect
        if not self.is_paired:
            await self.discover_and_connect()
        else:
            await self.request_current_assignment()
        
        # Keep running
        while True:
            await asyncio.sleep(0.1)

    def _send_nats_message(self, subject: str, data: dict, timeout: int = 5) -> Tuple[bool, str]:
        """Unified NATS message sending"""
        if not self.nats_client or not self.nats_loop:
            return False, "NATS not connected"
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.nats_client.publish(subject, json.dumps(data).encode()),
                self.nats_loop
            )
            future.result(timeout=timeout)
            return True, "Message sent"
        except Exception as e:
            return False, f"Error: {e}"

    # =============================================================================
    # MESSAGE HANDLERS
    # =============================================================================
    
    async def handle_response(self, msg):
        """Handle responses from hub"""
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get('type')
            print(f"Received response: {msg_type}")
            
            # Route to handlers
            handlers = {
                'paired': lambda: self._handle_paired(data),
                'connected': lambda: self._handle_connected(data),
                'assignment_update': lambda: self._handle_assignment_update(data),
                'timer_status': lambda: self._handle_timer_status(data),
                'script_list_response': lambda: self._handle_script_list(data),
                'script_toggle_response': lambda: self._handle_script_toggle(data),
                'remote_list_response': lambda: self._handle_remote_list(data),
                'shuffle_complete': lambda: self._handle_shuffle_complete(data),
                'shuffle_state': lambda: self._handle_shuffle_state(data),
                'scripts_updated': lambda: self._handle_scripts_updated(data),
                'execution_result': lambda: self._handle_execution_result(data),
                'debug_execution_result': lambda: self._handle_debug_execution_result(data)
            }
            
            handler = handlers.get(msg_type)
            if handler:
                handler()
            
        except Exception as e:
            print(f"Error handling response: {e}")

    async def handle_broadcast(self, msg):
        """Handle broadcast messages from hub"""
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get('type')
            print(f"Received broadcast: {msg_type}")
            
            if msg_type == 'assignments_broadcast':
                assignments = data.get('assignments', {})
                if self.remote_id in assignments:
                    old_command = self.assigned_command
                    self.assigned_command = assignments[self.remote_id]['command']
                    self.assignment_updated = True
                    print(f"Assignment updated via broadcast: {old_command} -> {self.assigned_command}")
                self.all_remotes = assignments
                
            elif msg_type == 'shuffle_state_broadcast':
                self.shuffle_state = data.get('state')
                print(f"Shuffle state broadcast: {self.shuffle_state}")
                
        except Exception as e:
            print(f"Error handling broadcast: {e}")

    # Response handlers - consolidated and simplified
    def _handle_paired(self, data):
        if data.get('success'):
            self.hub_token = data.get('hub_token')
            self.assigned_command = data.get('assigned_command')
            self.is_paired = True
            self.save_config()
            print(f"Successfully paired! Assigned command: {self.assigned_command}")
        else:
            print(f"Pairing failed: {data.get('message')}")

    def _handle_connected(self, data):
        if data.get('success'):
            self.hub_token = data.get('hub_id')
            self.hub_name = data.get('hub_name', 'Unknown Hub')
            self.assigned_command = data.get('assigned_command')
            self.is_paired = True
            self.save_config()
            print(f"Auto-connected to {self.hub_name}! Assigned command: {self.assigned_command}")
        else:
            print(f"Connection failed: {data.get('message')}")

    def _handle_assignment_update(self, data):
        self.assigned_command = data.get('assigned_command')
        self.assignment_updated = True
        if 'all_remotes' in data:
            self.all_remotes = data['all_remotes']
        print(f"Assignment updated: {self.assigned_command}")

    def _handle_timer_status(self, data):
        self.timer_enabled = data.get('timer_enabled', False)
        self.timer_minutes = data.get('timer_minutes', 10)
        print(f"Timer status: enabled={self.timer_enabled}, minutes={self.timer_minutes}")

    def _handle_script_list(self, data):
        self.available_scripts = data.get('scripts', [])
        print(f"Received script list: {len(self.available_scripts)} scripts")

    def _handle_script_toggle(self, data):
        if data.get('success'):
            script_name = data.get('script_name')
            enabled = data.get('enabled')
            print(f"Script '{script_name}' {'enabled' if enabled else 'disabled'}")

    def _handle_remote_list(self, data):
        self.hub_remote_list = data.get('remotes', [])
        print(f"Received remote list: {len(self.hub_remote_list)} remotes")

    def _handle_shuffle_complete(self, data):
        success = data.get('success')
        message = data.get('message')
        print(f"Shuffle {'completed' if success else 'failed'}: {message}")

    def _handle_shuffle_state(self, data):
        self.shuffle_state = data.get('state')
        print(f"Shuffle state: {self.shuffle_state}")

    def _handle_scripts_updated(self, data):
        success = data.get('success')
        message = data.get('message')
        print(f"Scripts update {'successful' if success else 'failed'}: {message}")

    def _handle_execution_result(self, data):
        success = data.get('success', False)
        message = data.get('message', 'No details')
        script_name = data.get('script_name', 'Unknown')
        print(f"Execution result for {script_name}: {'Success' if success else 'Failed'} - {message}")

    def _handle_debug_execution_result(self, data):
        success = data.get('success', False)
        message = data.get('message', 'No details')
        script_name = data.get('script_name', 'Unknown')
        print(f"Debug execution result for {script_name}: {'Success' if success else 'Failed'} - {message}")

    # =============================================================================
    # HUB DISCOVERY & CONNECTION
    # =============================================================================
    
    async def discover_hubs(self):
        """Discover available hubs on the network"""
        if not self.nats_client:
            return []
        
        try:
            inbox = self.nats_client.new_inbox()
            sub = await self.nats_client.subscribe(inbox, max_msgs=10)
            
            await self.nats_client.publish(
                f"{self.nats_config['subject_prefix']}.discover",
                b"",
                reply=inbox
            )
            
            # Collect responses for 3 seconds
            hubs = []
            start_time = time.time()
            
            while time.time() - start_time < 3:
                try:
                    msg = await asyncio.wait_for(sub.next_msg(), timeout=0.5)
                    hub_info = json.loads(msg.data.decode())
                    hubs.append(hub_info)
                    print(f"Found hub: {hub_info.get('hub_name')} ({hub_info.get('available_slots')}/{hub_info.get('total_slots')} slots)")
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"Error collecting hub responses: {e}")
            
            await sub.unsubscribe()
            return hubs
            
        except Exception as e:
            print(f"Error discovering hubs: {e}")
            return []

    async def discover_and_connect(self):
        """Discover and auto-connect to first available hub"""
        try:
            print("Discovering available hubs...")
            hubs = await self.discover_hubs()
            
            if not hubs:
                print("No hubs found. Will retry in 5 seconds...")
                await asyncio.sleep(5)
                await self.discover_and_connect()
                return
            
            # Find best hub
            best_hub = next((h for h in hubs if h.get('available_slots', 0) > 0 and h.get('active', True)), None)
            
            if not best_hub:
                print("No available hub slots. Will retry in 10 seconds...")
                await asyncio.sleep(10)
                await self.discover_and_connect()
                return
            
            print(f"Connecting to hub: {best_hub.get('hub_name', 'Unknown')}")
            
            # Send connection request
            connect_request = {
                "remote_id": self.remote_id,
                "username": self.username,
                "type": "connect",
                "timestamp": datetime.now().isoformat()
            }
            
            if self.nats_client:
                await self.nats_client.publish(
                    f"{self.nats_config['subject_prefix']}.connect",
                    json.dumps(connect_request).encode()
                )
            print(f"Sent connection request to {best_hub.get('hub_name')}")
            
        except Exception as e:
            print(f"Error in discover_and_connect: {e}")
            await asyncio.sleep(5)
            await self.discover_and_connect()

    async def request_current_assignment(self):
        """Request current assignment from hub on connection"""
        try:
            request = {
                "remote_id": self.remote_id,
                "hub_token": self.hub_token,
                "type": "request_assignment",
                "timestamp": datetime.now().isoformat()
            }
            
            if self.nats_client:
                await self.nats_client.publish(
                    f"{self.nats_config['subject_prefix']}.hub",
                    json.dumps(request).encode()
                )
            print("Requested current assignment from hub")
        except Exception as e:
            print(f"Error requesting assignment: {e}")

    # =============================================================================
    # CORE OPERATIONS
    # =============================================================================
    
    def pair_with_hub(self, pairing_code):
        """Attempt to pair with hub using pairing code or hub ID"""
        if not self.nats_client:
            return False, "Not connected to NATS"
        
        try:
            # Determine pairing type
            if pairing_code.startswith('HUB-') and len(pairing_code) == 12:
                pairing_request = {
                    "remote_id": self.remote_id,
                    "type": "pair",
                    "hub_id": pairing_code,
                    "direct": True,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                pairing_request = {
                    "remote_id": self.remote_id,
                    "type": "pair",
                    "code": pairing_code,
                    "timestamp": datetime.now().isoformat()
                }
            
            success, message = self._send_nats_message(
                f"{self.nats_config['subject_prefix']}.hub",
                pairing_request
            )
            
            if success:
                print("Pairing request sent via NATS")
                return True, "Pairing request sent to hub"
            else:
                return False, f"NATS publish failed: {message}"
            
        except Exception as e:
            return False, f"Error pairing: {e}"

    def press_button(self):
        """Send button press command to hub"""
        if not self.is_paired:
            return False, "Not paired with hub"
        
        if self.is_button_pressed:
            return False, "Button already pressed"
        
        self.is_button_pressed = True
        
        try:
            button_press = {
                "remote_id": self.remote_id,
                "type": "button_press",
                "hub_token": self.hub_token,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Sending button press for remote {self.remote_id}")
            print(f"Remote thinks assigned command is: {self.assigned_command}")
            
            success, message = self._send_nats_message(
                f"{self.nats_config['subject_prefix']}.hub",
                button_press,
                timeout=1
            )
            
            self.is_button_pressed = False
            
            if success:
                print("Button press sent via NATS")
                return True, "Command sent to hub successfully"
            else:
                return False, f"Error sending command: {message}"
            
        except Exception as e:
            self.is_button_pressed = False
            return False, f"Error sending command: {e}"

    def request_shuffle(self):
        """Request shuffle of all button assignments"""
        print(f"Shuffle request initiated by {self.remote_id}")
        
        if not self.nats_client:
            return False, "Not connected to NATS"
        
        try:
            shuffle_request = {
                "remote_id": self.remote_id,
                "hub_token": self.hub_token,
                "type": "shuffle_request",
                "timestamp": datetime.now().isoformat()
            }
            
            success, message = self._send_nats_message(
                f"{self.nats_config['subject_prefix']}.hub",
                shuffle_request
            )
            
            if success:
                print("Shuffle request sent successfully to hub")
                return True, "Shuffle request sent to hub"
            else:
                print(f"Error in shuffle request: {message}")
                return False, f"Error requesting shuffle: {message}"
            
        except Exception as e:
            print(f"Error in shuffle request: {e}")
            return False, f"Error requesting shuffle: {e}"

    def update_timer_settings(self, timer_enabled, timer_minutes):
        """Update timer settings on hub"""
        if not self.nats_client:
            return False, "Not connected to NATS"
        
        try:
            timer_update = {
                "remote_id": self.remote_id,
                "hub_token": self.hub_token,
                "type": "timer_update",
                "timer_enabled": timer_enabled,
                "timer_minutes": timer_minutes,
                "timestamp": datetime.now().isoformat()
            }
            
            success, message = self._send_nats_message(
                f"{self.nats_config['subject_prefix']}.hub",
                timer_update
            )
            
            if success:
                self.timer_enabled = timer_enabled
                self.timer_minutes = timer_minutes
                
                status = f"Timer {'enabled' if timer_enabled else 'disabled'}"
                if timer_enabled:
                    status += f" - shuffling every {timer_minutes} minutes"
                
                return True, status
            else:
                return False, f"Error updating timer: {message}"
            
        except Exception as e:
            return False, f"Error updating timer: {e}"

    def reset_pairing(self):
        """Reset pairing and clear stored data"""
        self.is_paired = False
        self.hub_token = ''
        self.assigned_command = ''
        self.is_connected = False
        self.save_config()
        return True, "Pairing reset successfully"

    # =============================================================================
    # NATS MESSAGE SENDERS (using unified sender)
    # =============================================================================
    
    def send_username_update(self, username):
        """Send username update to hub"""
        if self.is_paired and self.nats_client:
            try:
                username_update = {
                    "remote_id": self.remote_id,
                    "hub_token": self.hub_token,
                    "type": "username_update",
                    "username": username,
                    "timestamp": datetime.now().isoformat()
                }
                
                success, message = self._send_nats_message(
                    f"{self.nats_config['subject_prefix']}.hub",
                    username_update
                )
                
                if success:
                    print(f"Sent username update to hub: {username}")
                else:
                    print(f"Error sending username update: {message}")
                    
            except Exception as e:
                print(f"Error sending username update to hub: {e}")

    def send_script_list_request(self):
        """Request script list from hub"""
        script_request = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "script_list_request",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            script_request
        )

    def send_script_toggle(self, script_name, enabled):
        """Send script toggle request to hub"""
        toggle_request = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "script_toggle",
            "script_name": script_name,
            "enabled": enabled,
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            toggle_request
        )

    def send_remote_list_request(self):
        """Request remote list from hub"""
        remote_list_request = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "remote_list_request",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            remote_list_request
        )

    def send_heartbeat(self):
        """Send heartbeat to hub"""
        heartbeat_msg = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            heartbeat_msg,
            timeout=1
        )

    def send_script_update_request(self):
        """Request hub to update scripts from Git"""
        update_request = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "update_scripts_request",
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            update_request
        )

    def send_debug_execute_request(self, script_name):
        """Request hub to execute a specific script for debugging"""
        debug_request = {
            "remote_id": self.remote_id,
            "hub_token": self.hub_token,
            "type": "debug_execute_request",
            "script_name": script_name,
            "timestamp": datetime.now().isoformat()
        }
        
        return self._send_nats_message(
            f"{self.nats_config['subject_prefix']}.hub",
            debug_request
        )


# =============================================================================
# FLASK ROUTES
# =============================================================================

remote_app = OptimizedRemote()

@app.route('/')
def home():
    """Main page"""
    return render_template('index.html', 
                         remote_id=remote_app.remote_id,
                         is_paired=remote_app.is_paired,
                         assigned_command=remote_app.assigned_command,
                         is_connected=remote_app.is_connected)

@app.route('/api/status')
def get_status():
    """Get current app status"""
    assignment_updated = getattr(remote_app, 'assignment_updated', False)
    if assignment_updated:
        remote_app.assignment_updated = False
    
    return jsonify({
        'remote_id': remote_app.remote_id,
        'is_paired': remote_app.is_paired,
        'assigned_command': remote_app.assigned_command,
        'is_connected': remote_app.is_connected,
        'is_button_pressed': remote_app.is_button_pressed,
        'assignment_updated': assignment_updated,
        'shuffle_state': getattr(remote_app, 'shuffle_state', None)
    })

@app.route('/api/discover-hubs', methods=['GET'])
def discover_hubs():
    """Discover available hubs on the network"""
    try:
        if not remote_app.nats_loop or not remote_app.nats_client:
            return jsonify({'success': False, 'message': 'NATS not connected', 'hubs': []})
        
        future = asyncio.run_coroutine_threadsafe(
            remote_app.discover_hubs(),
            remote_app.nats_loop
        )
        
        hubs = future.result(timeout=3)
        return jsonify({'success': True, 'hubs': hubs})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error discovering hubs: {e}', 'hubs': []})

@app.route('/api/press', methods=['POST'])
def press_button():
    """Press the remote button"""
    success, message = remote_app.press_button()
    return jsonify({'success': success, 'message': message})

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset pairing"""
    success, message = remote_app.reset_pairing()
    return jsonify({'success': success, 'message': message})

@app.route('/api/shuffle', methods=['POST'])
def shuffle():
    """Request shuffle of all button assignments"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    success, message = remote_app.request_shuffle()
    return jsonify({
        'success': success,
        'message': message,
        'new_assignment': remote_app.assigned_command if success else None
    })

@app.route('/api/update-timer', methods=['POST'])
def update_timer():
    """Update timer settings"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    data = request.get_json()
    timer_enabled = data.get('timer_enabled', False)
    timer_minutes = data.get('timer_minutes', 10)
    
    success, message = remote_app.update_timer_settings(timer_enabled, timer_minutes)
    return jsonify({'success': success, 'message': message})

@app.route('/api/timer-status', methods=['GET'])
def timer_status():
    """Get current timer status from hub"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    return jsonify({
        'success': True,
        'timer_enabled': getattr(remote_app, 'timer_enabled', False),
        'timer_minutes': getattr(remote_app, 'timer_minutes', 10)
    })

@app.route('/api/remote-list', methods=['GET'])
def remote_list():
    """Get list of all connected remotes"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    try:
        remote_app.hub_remote_list = []  # Clear old data
        
        success, message = remote_app.send_remote_list_request()
        if not success:
            return jsonify({'success': False, 'message': f'NATS error: {message}'})
        
        # Return cached data (updated asynchronously)
        hub_remotes = getattr(remote_app, 'hub_remote_list', [])
        
        # Fallback to local data if hub data not available
        if not hub_remotes:
            all_remotes = getattr(remote_app, 'all_remotes', {})
            remote_list = []
            for remote_id, remote_data in all_remotes.items():
                remote_list.append({
                    'remote_id': remote_id,
                    'username': remote_data.get('username', ''),
                    'assigned_command': remote_data.get('command', 'Unknown'),
                    'last_seen': remote_data.get('last_seen', datetime.now().isoformat())
                })
            
            # Add ourselves if not present
            if not any(r['remote_id'] == remote_app.remote_id for r in remote_list):
                remote_list.append({
                    'remote_id': remote_app.remote_id,
                    'username': remote_app.username,
                    'assigned_command': remote_app.assigned_command,
                    'last_seen': datetime.now().isoformat()
                })
            hub_remotes = remote_list
        
        return jsonify({
            'success': True,
            'remotes': hub_remotes,
            'current_remote_id': remote_app.remote_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting remote list: {e}'})

@app.route('/api/update-username', methods=['POST'])
def update_username():
    """Update username for this remote"""
    data = request.get_json()
    username = data.get('username', '').strip()[:20]
    
    remote_app.username = username
    remote_app.save_config()
    remote_app.send_username_update(username)
    
    return jsonify({
        'success': True,
        'message': f'Username updated to: {username}' if username else 'Username cleared'
    })

@app.route('/api/script-list', methods=['GET'])
def get_script_list():
    """Get list of all available scripts from hub"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    try:
        remote_app.available_scripts = []  # Clear old data
        
        success, message = remote_app.send_script_list_request()
        if not success:
            return jsonify({'success': False, 'message': f'NATS error: {message}'})
        
        # Wait briefly for response
        max_wait = 3
        wait_interval = 0.1
        waited = 0
        
        while waited < max_wait:
            if hasattr(remote_app, 'available_scripts') and len(remote_app.available_scripts) > 0:
                break
            time.sleep(wait_interval)
            waited += wait_interval
        
        return jsonify({
            'success': True,
            'scripts': getattr(remote_app, 'available_scripts', [])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting script list: {e}'})

@app.route('/api/toggle-script', methods=['POST'])
def toggle_script():
    """Toggle a script's enabled/disabled state"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    data = request.get_json()
    script_name = data.get('script_name', '')
    enabled = data.get('enabled', True)
    
    if not script_name:
        return jsonify({'success': False, 'message': 'Script name required'})
    
    try:
        success, message = remote_app.send_script_toggle(script_name, enabled)
        if success:
            status = "enabled" if enabled else "disabled"
            return jsonify({'success': True, 'message': f'Script "{script_name}" {status}'})
        else:
            return jsonify({'success': False, 'message': f'NATS error: {message}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error toggling script: {e}'})

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    """Send heartbeat to hub to maintain connection"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired'})
    
    try:
        success, message = remote_app.send_heartbeat()
        return jsonify({'success': success, 'message': message if not success else None})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/update-scripts', methods=['POST'])
def update_scripts():
    """Request hub to update scripts from Git repository"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    try:
        success, message = remote_app.send_script_update_request()
        if success:
            return jsonify({'success': True, 'message': 'Script update request sent to hub'})
        else:
            return jsonify({'success': False, 'message': f'NATS error: {message}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error requesting script update: {e}'})

@app.route('/api/debug-execute', methods=['POST'])
def debug_execute():
    """Execute a specific script for debugging (bypasses normal assignment)"""
    if not remote_app.is_paired:
        return jsonify({'success': False, 'message': 'Not paired with hub'})
    
    data = request.get_json()
    script_name = data.get('script_name', '')
    
    if not script_name:
        return jsonify({'success': False, 'message': 'Script name required'})
    
    try:
        success, message = remote_app.send_debug_execute_request(script_name)
        if success:
            return jsonify({'success': True, 'message': f'Debug execution sent for {script_name}'})
        else:
            return jsonify({'success': False, 'message': f'NATS error: {message}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error executing script: {e}'})


def main():
    print(f"Starting Optimized Remote App - ID: {remote_app.remote_id}")
    print(f"Paired: {remote_app.is_paired}")
    if remote_app.is_paired:
        print(f"Assigned Command: {remote_app.assigned_command}")
    
    # Auto-open browser
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5001')
        print("Opened P_Buttons Remote in your default browser")
        print("If the browser didn't open automatically, go to: http://127.0.0.1:5001")
    
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, host='127.0.0.1', port=5001, use_reloader=False)

if __name__ == '__main__':
    main()