#!/usr/bin/env python3
"""
P_Buttons Hub - Optimized version with consolidated patterns
"""

import asyncio
import json
import os
import sys
import uuid
import logging
from datetime import datetime
import threading
import time
import hashlib
import random
from typing import Optional

import nats
from pynput import keyboard
try:
    from git import Repo
except ImportError:
    Repo = None

# Configuration paths (relative to project root)
CONFIG_FILE = "config/config.json"
SCRIPTS_DIR = "scripts"
LOGS_DIR = "logs"
PAIRED_REMOTES_FILE = "config/paired_remotes.json"
HUB_TOKEN_FILE = "config/hub_token.json"

class AutomationHub:
    def __init__(self):
        # Change to project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        
        # Setup
        self.setup_logging()
        self.setup_directories()
        
        # Load all configuration
        self.config = self._load_json(CONFIG_FILE, self._default_config())
        self.paired_remotes = self._load_json(PAIRED_REMOTES_FILE, {})
        self.disabled_scripts = set(self._load_json("config/disabled_scripts.json", []))
        self.hub_token = self._load_or_generate_token()
        self.hub_name = self._get_hub_name()
        
        # Runtime state  
        self.nats_client = None
        self.scripts_repo = None
        self.command_pool = []
        self.script_descriptions = {}
        self.hotkey_listener = None
        self.timer_enabled = False
        self.timer_minutes = 10
        self.timer_task = None
        self.hub_active = True
        
        # Initialize
        self._setup_git_repo()
        self._ensure_script_dependencies()
        self._load_command_pool()

    def setup_logging(self):
        """Setup logging with file and console handlers"""
        os.makedirs(LOGS_DIR, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{LOGS_DIR}/hub_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Hub starting...")

    def setup_directories(self):
        """Create necessary directories"""
        for directory in [SCRIPTS_DIR, LOGS_DIR]:
            os.makedirs(directory, exist_ok=True)

    # =============================================================================
    # UNIFIED CONFIG & PERSISTENCE 
    # =============================================================================
    
    def _load_json(self, file_path, default=None):
        """Unified JSON loading with error handling"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded {file_path}")
                    return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not load {file_path}: {e}")
        return default or {}

    def _save_json(self, file_path, data):
        """Unified JSON saving with error handling"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                self.logger.info(f"Saved {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")

    def _default_config(self):
        """Default configuration"""
        return {
            "nats_url": "nats://demo.nats.io:4222",
            "subject_prefix": "automation",
            "git_repo_url": "",
            "hotkey_combo": ["ctrl", "alt", "s", "p"],
            "command_timeout": 30,
            "max_remotes": 6
        }

    def _load_or_generate_token(self):
        """Load or generate hub token"""
        token_data = self._load_json(HUB_TOKEN_FILE)
        if token_data and 'token' in token_data:
            return token_data['token']
        
        # Generate new token
        machine_id = str(uuid.getnode())
        timestamp = str(int(time.time()))[:8]
        token_hash = hashlib.md5(f"{machine_id}-{timestamp}".encode()).hexdigest()[:8].upper()
        token = f"HUB-{token_hash}"
        
        self._save_json(HUB_TOKEN_FILE, {
            "token": token,
            "created": datetime.now().isoformat(),
            "version": "1.0"
        })
        return token

    def _get_hub_name(self):
        """Get friendly hub name"""
        import socket
        return socket.gethostname().split('.')[0].upper()[:20]

    def save_paired_remotes(self):
        """Save paired remotes"""
        self._save_json(PAIRED_REMOTES_FILE, self.paired_remotes)

    def save_disabled_scripts(self):
        """Save disabled scripts"""
        self._save_json("config/disabled_scripts.json", list(self.disabled_scripts))

    # =============================================================================
    # SCRIPT MANAGEMENT
    # =============================================================================
    
    def _setup_git_repo(self):
        """Setup Git repository for script management"""
        if not self.config.get("git_repo_url") or not Repo:
            return
            
        try:
            git_path = os.path.join(SCRIPTS_DIR, '.git')
            if os.path.exists(git_path):
                self.scripts_repo = Repo(SCRIPTS_DIR)
                self.logger.info("Git repository loaded")
            else:
                self.scripts_repo = Repo.init(SCRIPTS_DIR)
                self.scripts_repo.create_remote('origin', self.config["git_repo_url"])
                self.logger.info("Git repository initialized")
        except Exception as e:
            self.logger.error(f"Git setup error: {e}")

    def _scan_script_dependencies(self):
        """Scan all scripts for import statements and return required packages"""
        import re
        import ast
        
        required_packages = set()
        
        # Standard library modules (don't need to install these)
        stdlib_modules = {
            'os', 'sys', 'time', 'random', 'subprocess', 'json', 'hashlib', 'uuid',
            'datetime', 'threading', 'logging', 'tempfile', 'base64', 'ctypes',
            're', 'ast', 'collections', 'itertools', 'functools', 'pathlib', 'winsound'
        }
        
        # Package name mappings for imports that don't match pip package names
        package_mappings = {
            'win32api': 'pywin32',
            'win32con': 'pywin32',
            'cv2': 'opencv-python',
            'PIL': 'Pillow'
        }
        
        for file_name in os.listdir(SCRIPTS_DIR):
            if file_name.endswith('.py'):
                file_path = os.path.join(SCRIPTS_DIR, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse imports using AST
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name.split('.')[0]
                                if module not in stdlib_modules:
                                    pkg = package_mappings.get(module, module)
                                    required_packages.add(pkg)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                module = node.module.split('.')[0]
                                if module not in stdlib_modules:
                                    pkg = package_mappings.get(module, module)
                                    required_packages.add(pkg)
                                    
                except Exception as e:
                    self.logger.warning(f"Could not scan {file_name} for dependencies: {e}")
        
        return list(required_packages)

    def _ensure_script_dependencies(self):
        """Auto-scan scripts and install missing dependencies"""
        try:
            # Scan all scripts for required packages
            required_packages = self._scan_script_dependencies()
            
            if not required_packages:
                self.logger.info("No external dependencies found in scripts")
                return
            
            self.logger.info(f"Found script dependencies: {', '.join(required_packages)}")
            
            # Update requirements.txt
            requirements_file = os.path.join(SCRIPTS_DIR, "requirements.txt")
            with open(requirements_file, 'w') as f:
                for package in sorted(required_packages):
                    f.write(f"{package}\n")
            
            # Install using uv if available, fallback to pip
            try:
                result = subprocess.run([
                    sys.executable, "-m", "uv", "pip", "sync", requirements_file
                ], capture_output=True, text=True, timeout=120)
                installer = "uv"
            except (FileNotFoundError, subprocess.CalledProcessError):
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", requirements_file
                ], capture_output=True, text=True, timeout=120)
                installer = "pip"
            
            if result.returncode == 0:
                self.logger.info(f"Dependencies installed successfully using {installer}")
            else:
                self.logger.error(f"Dependency installation failed: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Failed to manage dependencies: {e}")

    def _extract_script_description(self, file_path, ext):
        """Extract description from script file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:10]
            
            # Look for descriptions based on file type
            for line in lines:
                line = line.strip()
                if ext == '.py' and (line.startswith('"""') or line.startswith('#')):
                    return line.replace('"""', '').replace('#', '').strip()[:100]
                elif ext == '.ps1' and line.startswith('#'):
                    return line.replace('#', '').strip()[:100]
                elif ext == '.bat' and line.startswith('REM'):
                    return line.replace('REM', '').strip()[:100]
            
            # Fallback based on filename
            name_lower = file_path.lower()
            fallbacks = {
                'minimize': "Minimizes all windows temporarily",
                'mouse': "Moves the mouse cursor randomly", 
                'sound': "Plays a sound effect",
                'rotate': "Rotates the screen orientation",
                'screen': "Rotates the screen orientation",
                'message': "Shows a system notification message",
                'system': "Shows a system notification message",
                'desktop': "Desktop automation effect",
                'maintenance': "Desktop automation effect"
            }
            
            for keyword, description in fallbacks.items():
                if keyword in name_lower:
                    return description
                    
            return "Automation script"
        except Exception:
            return "Unable to read description"

    def _load_command_pool(self):
        """Load available scripts"""
        self.command_pool = []
        self.script_descriptions = {}
        
        if not os.path.exists(SCRIPTS_DIR):
            return
            
        for file_name in os.listdir(SCRIPTS_DIR):
            if file_name.startswith('.') or file_name.endswith('.md'):
                continue
                
            file_path = os.path.join(SCRIPTS_DIR, file_name)
            if os.path.isfile(file_path):
                _, ext = os.path.splitext(file_name)
                if ext.lower() in ['.py', '.ps1', '.bat', '.exe']:
                    self.command_pool.append(file_name)
                    self.script_descriptions[file_name] = self._extract_script_description(file_path, ext)
                    
        self.logger.info(f"Loaded {len(self.command_pool)} scripts")

    def get_enabled_scripts(self):
        """Get enabled scripts only"""
        return [s for s in self.command_pool if s not in self.disabled_scripts]

    def update_scripts_from_git(self):
        """Pull latest scripts from Git and reload command pool"""
        if not self.scripts_repo:
            return False, "Git repository not configured"
        
        try:
            # Pull latest changes
            origin = self.scripts_repo.remotes.origin
            origin.pull()
            self.logger.info("Pulled latest changes from Git repository")
            
            # Check for new dependencies
            self._ensure_script_dependencies()
            
            # Reload command pool
            old_count = len(self.command_pool)
            self._load_command_pool()
            new_count = len(self.command_pool)
            
            # Reassign commands if needed
            self._ensure_unique_assignments()
            
            message = f"Updated scripts: {old_count} → {new_count} scripts"
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            error_msg = f"Git update failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    # =============================================================================
    # REMOTE MANAGEMENT
    # =============================================================================
    
    def cleanup_offline_remotes(self):
        """Remove offline remotes (5+ minutes)"""
        current_time = datetime.now()
        offline_remotes = []
        
        for remote_id, remote_data in self.paired_remotes.items():
            try:
                last_seen = datetime.fromisoformat(remote_data.get('last_seen', ''))
                if (current_time - last_seen).total_seconds() > 300:
                    offline_remotes.append(remote_id)
            except ValueError:
                offline_remotes.append(remote_id)
        
        for remote_id in offline_remotes:
            del self.paired_remotes[remote_id]
            self.logger.info(f"Removed offline remote: {remote_id}")
        
        if offline_remotes:
            self.save_paired_remotes()
            self._ensure_unique_assignments()

    def _ensure_unique_assignments(self):
        """Ensure unique command assignments"""
        if not self.paired_remotes:
            return
        
        enabled_scripts = self.get_enabled_scripts()
        assignments = {}
        duplicates = []
        
        # Find duplicates
        for remote_id, remote_data in self.paired_remotes.items():
            cmd = remote_data.get('assigned_command', '')
            if cmd in assignments:
                duplicates.append(remote_id)
            else:
                assignments[cmd] = remote_id
        
        # Reassign duplicates
        for remote_id in duplicates:
            for cmd in enabled_scripts:
                if cmd not in assignments:
                    self.paired_remotes[remote_id]['assigned_command'] = cmd
                    assignments[cmd] = remote_id
                    break
        
        if duplicates:
            self.save_paired_remotes()

    def _assign_command_to_remote(self, remote_id):
        """Assign random command to remote"""
        enabled_scripts = self.get_enabled_scripts()
        if not enabled_scripts:
            return "No enabled commands available"
            
        # Avoid duplicates if possible
        used = [r['assigned_command'] for r in self.paired_remotes.values()]
        available = [s for s in enabled_scripts if s not in used] or enabled_scripts
        
        command = random.choice(available)
        self.logger.info(f"Assigned '{command}' to {remote_id}")
        return command

    # =============================================================================
    # TIMER SYSTEM
    # =============================================================================
    
    async def _start_shuffle_timer(self):
        """Start shuffle timer"""
        if self.timer_task:
            self.timer_task.cancel()
        
        if self.timer_enabled and self.timer_minutes > 0:
            async def timer_loop():
                while self.timer_enabled:
                    await asyncio.sleep(self.timer_minutes * 60)
                    if self.timer_enabled:
                        success, _ = self._shuffle_all_assignments()
                        if success:
                            await self._broadcast_assignments()
            
            self.timer_task = asyncio.create_task(timer_loop())
            self.logger.info(f"Timer started: {self.timer_minutes}min intervals")

    async def _stop_shuffle_timer(self):
        """Stop shuffle timer"""
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
            self.logger.info("Timer stopped")

    # =============================================================================
    # HOTKEY SYSTEM
    # =============================================================================
    
    def setup_hotkey(self):
        """Setup Ctrl+Alt+S+P hotkey"""
        try:
            def show_info():
                print("\n=== HUB INFO ===")
                print(f"Name: {self.hub_name}")
                print(f"ID: {self.hub_token}")
                print(f"Remotes: {len(self.paired_remotes)}")
                print(f"Active: {'YES' if self.hub_active else 'NO'}")
                print("================\n")
                
            hotkey = keyboard.HotKey(keyboard.HotKey.parse('<ctrl>+<alt>+s+p'), show_info)
            self.hotkey_listener = keyboard.Listener(
                on_press=lambda k: hotkey.press(k) if k else None,
                on_release=lambda k: hotkey.release(k) if k else None
            )
            self.hotkey_listener.start()
            self.logger.info("Hotkey registered: Ctrl+Alt+S+P")
        except Exception as e:
            self.logger.error(f"Hotkey setup error: {e}")

    # =============================================================================
    # CORE OPERATIONS
    # =============================================================================
    
    async def _execute_command(self, command_name):
        """Execute script command"""
        if command_name not in self.command_pool:
            return False, "Command not found"
            
        command_path = os.path.join(SCRIPTS_DIR, command_name)
        if not os.path.exists(command_path):
            return False, "File not found"
            
        try:
            _, ext = os.path.splitext(command_name)
            
            # Build command based on extension
            cmd_map = {
                '.py': [sys.executable, command_path],
                '.ps1': ['powershell', '-ExecutionPolicy', 'Bypass', '-File', command_path],
                '.bat': [command_path],
                '.exe': [command_path]
            }
            
            if ext.lower() not in cmd_map:
                return False, "Unsupported file type"
            
            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd_map[ext.lower()],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.get("command_timeout", 30)
                )
            except asyncio.TimeoutError:
                process.kill()
                return False, "Timeout"
                
            duration = int((time.time() - start_time) * 1000)
            
            if process.returncode == 0:
                self.logger.info(f"Executed {command_name} in {duration}ms")
                return True, f"Success ({duration}ms)"
            else:
                error = stderr.decode()[:100] if stderr else "Unknown error"
                self.logger.error(f"{command_name} failed: {error}")
                return False, f"Failed: {error}"
                
        except Exception as e:
            return False, f"Error: {e}"

    def _shuffle_all_assignments(self):
        """Shuffle command assignments"""
        if not self.paired_remotes:
            return False, "No remotes"
        
        enabled_scripts = self.get_enabled_scripts()
        if len(enabled_scripts) < len(self.paired_remotes):
            return False, "Not enough scripts"
        
        remote_ids = list(self.paired_remotes.keys())
        shuffled = random.sample(enabled_scripts, len(remote_ids))
        
        for i, remote_id in enumerate(remote_ids):
            old = self.paired_remotes[remote_id]['assigned_command']
            new = shuffled[i]
            self.paired_remotes[remote_id]['assigned_command'] = new
            self.logger.info(f"{remote_id}: {old} -> {new}")
        
        self.save_paired_remotes()
        return True, f"Shuffled {len(remote_ids)} assignments"

    # =============================================================================
    # NATS COMMUNICATION
    # =============================================================================
    
    async def handle_message(self, msg):
        """Main message router"""
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get('type')
            remote_id = data.get('remote_id')
            
            # Update last seen
            if remote_id in self.paired_remotes:
                self.paired_remotes[remote_id]['last_seen'] = datetime.now().isoformat()
            
            # Route to handlers
            handlers = {
                'pair': lambda: self._handle_pair(data, remote_id),
                'button_press': lambda: self._handle_button_press(data, remote_id),
                'shuffle_request': lambda: self._handle_shuffle(data, remote_id),
                'timer_update': lambda: self._handle_timer_update(data, remote_id),
                'script_list_request': lambda: self._handle_script_list(data, remote_id),
                'script_toggle': lambda: self._handle_script_toggle(data, remote_id),
                'remote_list_request': lambda: self._handle_remote_list(data, remote_id),
                'username_update': lambda: self._handle_username_update(data, remote_id),
                'heartbeat': lambda: self._handle_heartbeat(data, remote_id),
                'request_assignment': lambda: self._handle_assignment_request(data, remote_id),
                'update_scripts_request': lambda: self._handle_script_update(data, remote_id),
                'debug_execute_request': lambda: self._handle_debug_execute(data, remote_id)
            }
            
            handler = handlers.get(msg_type)
            if handler:
                await handler()
            else:
                self.logger.warning(f"Unknown message: {msg_type}")
                
        except Exception as e:
            self.logger.error(f"Message error: {e}")

    async def _send_response(self, remote_id, response_data):
        """Send response to remote"""
        if self.nats_client:
            subject = f"{self.config['subject_prefix']}.response.{remote_id}"
            await self.nats_client.publish(subject, json.dumps(response_data).encode())

    async def _broadcast_assignments(self):
        """Broadcast assignments to all remotes"""
        if not self.nats_client:
            return
        
        assignments = {
            rid: {
                'command': data['assigned_command'],
                'username': data.get('username', '')
            } for rid, data in self.paired_remotes.items()
        }
        
        broadcast = {
            'type': 'assignments_broadcast',
            'assignments': assignments,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.nats_client.publish(
            f"{self.config['subject_prefix']}.broadcast",
            json.dumps(broadcast).encode()
        )

    async def _broadcast_shuffle_state(self, state):
        """Broadcast shuffle state"""
        if self.nats_client:
            message = {
                'type': 'shuffle_state_broadcast',
                'state': state,
                'timestamp': datetime.now().isoformat()
            }
            await self.nats_client.publish(
                f"{self.config['subject_prefix']}.broadcast",
                json.dumps(message).encode()
            )

    # Message handlers - consolidated and simplified
    async def _handle_pair(self, data, remote_id):
        hub_id = data.get('hub_id')
        if hub_id == self.hub_token and len(self.paired_remotes) < self.config.get('max_remotes', 6):
            command = self._assign_command_to_remote(remote_id)
            self.paired_remotes[remote_id] = {
                "remote_id": remote_id,
                "hub_token": self.hub_token,
                "assigned_command": command,
                "paired_at": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "username": ""
            }
            self.save_paired_remotes()
            response = {'type': 'paired', 'success': True, 'hub_token': self.hub_token, 'assigned_command': command}
        else:
            response = {'type': 'paired', 'success': False, 'message': 'Connection failed'}
        
        await self._send_response(remote_id, response)

    async def _handle_button_press(self, data, remote_id):
        if not self.hub_active:
            response = {'type': 'execution_result', 'success': False, 'message': 'Hub inactive'}
        elif remote_id in self.paired_remotes and data.get('hub_token') == self.hub_token:
            command = self.paired_remotes[remote_id].get('assigned_command')
            success, message = await self._execute_command(command)
            response = {
                'type': 'execution_result',
                'success': success,
                'message': message,
                'script_name': command,
                'timestamp': datetime.now().isoformat()
            }
        else:
            response = {'type': 'execution_result', 'success': False, 'message': 'Not authorized'}
        
        await self._send_response(remote_id, response)

    async def _handle_shuffle(self, data, remote_id):
        if remote_id in self.paired_remotes:
            await self._broadcast_shuffle_state('start')
            success, message = self._shuffle_all_assignments()
            if success:
                await self._broadcast_assignments()
            await self._broadcast_shuffle_state('end')
            
            response = {'type': 'shuffle_complete', 'success': success, 'message': message}
            await self._send_response(remote_id, response)

    async def _handle_timer_update(self, data, remote_id):
        if remote_id in self.paired_remotes:
            self.timer_enabled = data.get('timer_enabled', False)
            self.timer_minutes = data.get('timer_minutes', 10)
            
            if self.timer_enabled:
                await self._start_shuffle_timer()
            else:
                await self._stop_shuffle_timer()
            
            # Broadcast to all
            for rid in self.paired_remotes.keys():
                timer_response = {
                    'type': 'timer_status',
                    'timer_enabled': self.timer_enabled,
                    'timer_minutes': self.timer_minutes
                }
                await self._send_response(rid, timer_response)

    async def _handle_script_list(self, data, remote_id):
        if remote_id in self.paired_remotes:
            scripts = [{'name': s, 'enabled': s not in self.disabled_scripts} for s in self.command_pool]
            response = {'type': 'script_list_response', 'scripts': scripts}
            await self._send_response(remote_id, response)

    async def _handle_script_toggle(self, data, remote_id):
        if remote_id in self.paired_remotes:
            script_name = data.get('script_name')
            enabled = data.get('enabled', True)
            
            if script_name in self.command_pool:
                if enabled:
                    self.disabled_scripts.discard(script_name)
                else:
                    self.disabled_scripts.add(script_name)
                
                self.save_disabled_scripts()
                self._shuffle_all_assignments()
                await self._broadcast_assignments()
                
                response = {
                    'type': 'script_toggle_response',
                    'success': True,
                    'script_name': script_name,
                    'enabled': enabled
                }
            else:
                response = {'type': 'script_toggle_response', 'success': False, 'message': 'Script not found'}
            
            await self._send_response(remote_id, response)

    async def _handle_remote_list(self, data, remote_id):
        if remote_id in self.paired_remotes:
            remotes = [{
                'remote_id': rid,
                'username': rdata.get('username', ''),
                'assigned_command': rdata.get('assigned_command', ''),
                'last_seen': rdata.get('last_seen', '')
            } for rid, rdata in self.paired_remotes.items()]
            
            response = {'type': 'remote_list_response', 'remotes': remotes}
            await self._send_response(remote_id, response)

    async def _handle_username_update(self, data, remote_id):
        if remote_id in self.paired_remotes:
            self.paired_remotes[remote_id]['username'] = data.get('username', '')
            self.save_paired_remotes()

    async def _handle_heartbeat(self, data, remote_id):
        # Just update last_seen (already done in main handler)
        pass

    async def _handle_assignment_request(self, data, remote_id):
        if remote_id in self.paired_remotes and data.get('hub_token') == self.hub_token:
            command = self.paired_remotes[remote_id].get('assigned_command', '')
            response = {'type': 'assignment_update', 'assigned_command': command}
            await self._send_response(remote_id, response)

    async def _handle_script_update(self, data, remote_id):
        if remote_id in self.paired_remotes:
            success, message = self.update_scripts_from_git()
            
            if success:
                # Broadcast updated assignments to all remotes
                await self._broadcast_assignments()
            
            response = {
                'type': 'scripts_updated',
                'success': success,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            await self._send_response(remote_id, response)

    async def _handle_debug_execute(self, data, remote_id):
        if remote_id in self.paired_remotes and data.get('hub_token') == self.hub_token:
            script_name = data.get('script_name')
            if script_name in self.command_pool:
                success, message = await self._execute_command(script_name)
                response = {
                    'type': 'debug_execution_result',
                    'success': success,
                    'message': message,
                    'script_name': script_name,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                response = {
                    'type': 'debug_execution_result',
                    'success': False,
                    'message': 'Script not found',
                    'script_name': script_name,
                    'timestamp': datetime.now().isoformat()
                }
            await self._send_response(remote_id, response)

    async def handle_discovery(self, msg):
        """Handle hub discovery"""
        try:
            hub_info = {
                'hub_id': self.hub_token,
                'hub_name': self.hub_name,
                'available_slots': self.config.get('max_remotes', 6) - len(self.paired_remotes),
                'total_slots': self.config.get('max_remotes', 6),
                'active': self.hub_active,
                'scripts_count': len(self.get_enabled_scripts())
            }
            
            if msg.reply and self.nats_client:
                await self.nats_client.publish(msg.reply, json.dumps(hub_info).encode())
        except Exception as e:
            self.logger.error(f"Discovery error: {e}")

    async def handle_connection(self, msg):
        """Handle auto-connection requests"""
        try:
            data = json.loads(msg.data.decode())
            remote_id = data.get('remote_id')
            
            if len(self.paired_remotes) >= self.config.get('max_remotes', 6):
                response = {'type': 'connected', 'success': False, 'message': 'Hub full'}
            else:
                if remote_id not in self.paired_remotes:
                    command = self._assign_command_to_remote(remote_id)
                    self.paired_remotes[remote_id] = {
                        "remote_id": remote_id,
                        "hub_token": self.hub_token,
                        "assigned_command": command,
                        "paired_at": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat(),
                        "username": data.get('username', '')
                    }
                    self.save_paired_remotes()
                else:
                    command = self.paired_remotes[remote_id]['assigned_command']
                
                response = {
                    'type': 'connected',
                    'success': True,
                    'hub_id': self.hub_token,
                    'hub_name': self.hub_name,
                    'assigned_command': command
                }
            
            if self.nats_client:
                await self.nats_client.publish(f"{self.config['subject_prefix']}.response.{remote_id}", json.dumps(response).encode())
            await self._broadcast_assignments()
        except Exception as e:
            self.logger.error(f"Connection error: {e}")

    # =============================================================================
    # MAIN EXECUTION
    # =============================================================================
    
    async def run(self):
        """Main run loop"""
        try:
            # Connect to NATS
            self.logger.info(f"Connecting to NATS: {self.config['nats_url']}")
            self.nats_client = await nats.connect(self.config['nats_url'])
            
            # Subscribe to subjects
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.hub", cb=self.handle_message)
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.connect", cb=self.handle_connection)
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.discover", cb=self.handle_discovery)
            
            self.setup_hotkey()
            
            self.logger.info(f"Hub {self.hub_name} ({self.hub_token}) running with {len(self.command_pool)} scripts")
            
            # Console handler
            def console_handler():
                commands = {'on': lambda: setattr(self, 'hub_active', True), 'off': lambda: setattr(self, 'hub_active', False)}
                while True:
                    try:
                        cmd = input().strip().lower()
                        if cmd in commands:
                            commands[cmd]()
                            print(f"Hub {'ACTIVE' if self.hub_active else 'INACTIVE'}")
                        elif cmd in ['help', '?']:
                            print("Commands: on/off, help, status, info")
                        elif cmd == 'status':
                            print(f"Active: {self.hub_active}, Remotes: {len(self.paired_remotes)}, Scripts: {len(self.get_enabled_scripts())}")
                        elif cmd == 'info':
                            print(f"Name: {self.hub_name}, ID: {self.hub_token}")
                    except (EOFError, KeyboardInterrupt):
                        break
            
            threading.Thread(target=console_handler, daemon=True).start()
            
            # Keep running
            while True:
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            if self.nats_client:
                await self.nats_client.close()
            if self.hotkey_listener:
                self.hotkey_listener.stop()

def main():
    try:
        hub = AutomationHub()
        asyncio.run(hub.run())
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()