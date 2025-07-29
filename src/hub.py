#!/usr/bin/env python3
"""
P_Buttons Hub - Optimized version with consolidated patterns
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import secrets
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime

import nats
from flask import Flask, jsonify, render_template, request
from pynput import keyboard

try:
    from git import Repo
except ImportError:
    Repo = None

import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

# Configuration paths (relative to project root)
CONFIG_FILE = "config/config.json"
SCRIPTS_DIR = "scripts"
LOGS_DIR = "logs"
PAIRED_REMOTES_FILE = "config/paired_remotes.json"
HUB_TOKEN_FILE = "config/hub_token.json"

# Unique namespace for this deployment (hardcoded for cross-network discovery)
DEPLOYMENT_NAMESPACE = "prank_deployment_x7k9m_2025"

# =============================================================================
# FLASK WEB UI SETUP
# =============================================================================

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


# UV Configuration
UV_DIR = "uv_embedded"
UV_EXE = os.path.join(UV_DIR, "uv.exe")
UV_DOWNLOAD_URL = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"


class UVManager:
    """Manages embedded UV installation and Python environment"""

    def __init__(self, logger):
        self.logger = logger
        self.uv_dir = Path(UV_DIR)
        self.uv_exe = Path(UV_EXE)

    async def ensure_uv_available(self):
        """Ensure UV is available, download if needed"""
        if self.uv_exe.exists():
            self.logger.info("UV already available")
            return True

        self.logger.info("UV not found, downloading...")
        return await self._download_and_setup_uv()

    async def _download_and_setup_uv(self):
        """Download and extract UV binary"""
        try:
            # Create UV directory
            self.uv_dir.mkdir(exist_ok=True)

            # Download UV
            zip_path = self.uv_dir / "uv.zip"
            self.logger.info(f"Downloading UV from {UV_DOWNLOAD_URL}")

            urllib.request.urlretrieve(UV_DOWNLOAD_URL, zip_path)

            # Extract UV
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.uv_dir)

            # Find the extracted uv.exe (might be in subdirectory)
            extracted_uv = None
            for file_path in self.uv_dir.rglob("uv.exe"):
                extracted_uv = file_path
                break

            if extracted_uv:
                # Move to expected location
                if extracted_uv != self.uv_exe:
                    shutil.move(str(extracted_uv), str(self.uv_exe))

                # Clean up
                zip_path.unlink()

                # Remove any extracted directories
                for item in self.uv_dir.iterdir():
                    if item.is_dir() and item.name != "cache":
                        shutil.rmtree(item)

                self.logger.info("UV successfully downloaded and setup")
                return True
            else:
                self.logger.error("Could not find uv.exe in downloaded archive")
                return False

        except Exception as e:
            self.logger.error(f"Failed to download UV: {e}")
            return False

    async def ensure_python_environment(self):
        """Ensure Python environment is ready with all dependencies"""
        if not self.uv_exe.exists():
            return False

        try:
            # Check if project dependencies are installed
            result = subprocess.run([
                str(self.uv_exe), "sync", "--frozen"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                self.logger.info("Python environment ready")
                return True
            else:
                self.logger.info("Installing Python environment...")
                # Install dependencies
                result = subprocess.run([
                    str(self.uv_exe), "sync"
                ], capture_output=True, text=True, timeout=300)

                if result.returncode == 0:
                    self.logger.info("Python environment setup complete")
                    return True
                else:
                    self.logger.error(f"Failed to setup Python environment: {result.stderr}")
                    return False

        except Exception as e:
            self.logger.error(f"Error setting up Python environment: {e}")
            return False

    def run_script_with_uv(self, script_path):
        """Run a Python script using embedded UV"""
        if not self.uv_exe.exists():
            raise RuntimeError("UV not available")

        return subprocess.run([
            str(self.uv_exe), "run", "python", script_path
        ], capture_output=True, text=True, timeout=30)

class AutomationHub:
    def __init__(self):
        # Change to project root directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)

        # Setup
        self.setup_logging()
        self.setup_directories()
        
        # Web UI state
        self.web_ui_port = 5000
        self.web_thread = None

        # Initialize UV Manager
        self.uv_manager = UVManager(self.logger)

        # Load all configuration
        self.config = self._load_json(CONFIG_FILE, self._default_config())
        # Override subject_prefix with hardcoded namespace for cross-network discovery
        self.config['subject_prefix'] = DEPLOYMENT_NAMESPACE
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
        self.shutdown_requested = False

        # Initialize
        self._setup_git_repo()
        self._load_scripts_hybrid()
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
        for directory in [SCRIPTS_DIR, LOGS_DIR, "config"]:
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

    def _load_scripts_hybrid(self):
        """Hybrid script loading: Try Git first, fall back to bundled scripts"""
        scripts_loaded = False
        
        # Method 1: Try to update from Git if available
        if self.scripts_repo and self.config.get("git_repo_url"):
            try:
                origin = self.scripts_repo.remotes.origin
                origin.pull()
                self.logger.info("Successfully pulled latest scripts from Git")
                scripts_loaded = True
            except Exception as e:
                self.logger.warning(f"Git pull failed, will use bundled scripts: {e}")
        
        # Method 2: Fall back to bundled scripts if Git failed
        if not scripts_loaded:
            try:
                self._extract_bundled_scripts()
                self.logger.info("Using bundled scripts as fallback")
            except Exception as e:
                self.logger.error(f"Failed to extract bundled scripts: {e}")

    def _extract_bundled_scripts(self):
        """Extract bundled scripts from PyInstaller bundle"""
        import sys
        
        # Check if running as PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            bundled_scripts_dir = os.path.join(sys._MEIPASS, 'scripts')
            if os.path.exists(bundled_scripts_dir):
                # Ensure local scripts directory exists
                os.makedirs(SCRIPTS_DIR, exist_ok=True)
                
                # Copy bundled scripts to local directory
                for item in os.listdir(bundled_scripts_dir):
                    if item.startswith('.'):
                        continue
                    src = os.path.join(bundled_scripts_dir, item)
                    dst = os.path.join(SCRIPTS_DIR, item)
                    
                    # Only copy if doesn't exist or bundled is newer
                    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
                        elif os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                
                self.logger.info("Extracted bundled scripts to local directory")
            else:
                self.logger.warning("No bundled scripts found in PyInstaller bundle")
        else:
            # Development mode - scripts are already in place
            self.logger.info("Running in development mode, using local scripts")

    def _scan_script_dependencies(self):
        """Scan all scripts for import statements and return required packages"""
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
        """Remove offline remotes (2+ minutes)"""
        current_time = datetime.now()
        offline_remotes = []

        for remote_id, remote_data in self.paired_remotes.items():
            try:
                last_seen = datetime.fromisoformat(remote_data.get('last_seen', ''))
                if (current_time - last_seen).total_seconds() > 120:  # 2 minutes instead of 5
                    offline_remotes.append(remote_id)
            except ValueError:
                # Invalid timestamp, remove it
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
            if ext.lower() == '.py':
                # Use UV for Python scripts if available, fallback to system Python
                if self.uv_manager.uv_exe.exists():
                    cmd = [str(self.uv_manager.uv_exe), "run", "python", command_path]
                else:
                    cmd = [sys.executable, command_path]
            elif ext.lower() == '.ps1':
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', command_path]
            elif ext.lower() == '.bat':
                cmd = [command_path]
            elif ext.lower() == '.exe':
                cmd = [command_path]
            else:
                return False, "Unsupported file type"

            start_time = time.time()
            process = await asyncio.create_subprocess_exec(
                *cmd,
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
                'shutdown_hub': lambda: self._handle_shutdown(data, remote_id),
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

    async def _handle_shutdown(self, data, remote_id):
        """Handle shutdown request from remote"""
        if remote_id in self.paired_remotes:
            self.logger.info(f"Shutdown requested by {remote_id}")
            
            # Send confirmation to the requesting remote
            response = {
                'type': 'shutdown_confirmed',
                'message': 'Hub is shutting down'
            }
            await self._send_response(remote_id, response)
            
            # Notify all other remotes
            for rid in self.paired_remotes.keys():
                if rid != remote_id:
                    notify = {
                        'type': 'hub_shutting_down',
                        'message': f'Hub shutdown initiated by {self.paired_remotes[remote_id].get("username", remote_id)}'
                    }
                    await self._send_response(rid, notify)
            
            # Set shutdown flag
            self.shutdown_requested = True
            self.logger.info("Hub shutdown initiated")

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
            self.logger.info("Discovery request received")
            hub_info = {
                'hub_id': self.hub_token,
                'hub_name': self.hub_name,
                'available_slots': self.config.get('max_remotes', 6) - len(self.paired_remotes),
                'total_slots': self.config.get('max_remotes', 6),
                'active': self.hub_active,
                'scripts_count': len(self.get_enabled_scripts())
            }

            if msg.reply and self.nats_client:
                self.logger.info(f"Sending discovery response to {msg.reply}")
                await self.nats_client.publish(msg.reply, json.dumps(hub_info).encode())
            else:
                self.logger.warning("No reply address in discovery message")
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
            # Setup UV environment first
            self.logger.info("Setting up UV environment...")
            if not await self.uv_manager.ensure_uv_available():
                self.logger.error("Failed to setup UV - scripts may not work")
            elif not await self.uv_manager.ensure_python_environment():
                self.logger.error("Failed to setup Python environment - scripts may not work")
            else:
                self.logger.info("UV environment ready")

            # Connect to NATS
            self.logger.info(f"Connecting to NATS: {self.config['nats_url']}")
            self.nats_client = await nats.connect(self.config['nats_url'])

            # Subscribe to subjects
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.hub", cb=self.handle_message)
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.connect", cb=self.handle_connection)
            await self.nats_client.subscribe(f"{self.config['subject_prefix']}.discover", cb=self.handle_discovery)

            self.setup_hotkey()
            
            # Start web UI
            self.start_web_ui()

            self.logger.info(f"Hub {self.hub_name} ({self.hub_token}) running with {len(self.command_pool)} scripts")
            
            # Write hub info to file for debugging when running without console
            hub_info_file = os.path.join(LOGS_DIR, "hub_info.txt")
            with open(hub_info_file, 'w') as f:
                f.write(f"Hub Name: {self.hub_name}\n")
                f.write(f"Hub Token: {self.hub_token}\n")
                f.write(f"Scripts: {len(self.command_pool)}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")

            # Keep running
            while not self.shutdown_requested:
                await asyncio.sleep(1)
            
            self.logger.info("Shutdown requested via remote command")

        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            if self.nats_client:
                await self.nats_client.close()
            if self.hotkey_listener:
                self.hotkey_listener.stop()
    
    def start_web_ui(self):
        """Start Flask web UI in background thread"""
        def run_web_ui():
            try:
                app.run(debug=False, host='127.0.0.1', port=self.web_ui_port, use_reloader=False, threaded=True)
            except Exception as e:
                self.logger.error(f"Web UI error: {e}")
        
        self.web_thread = threading.Thread(target=run_web_ui, daemon=True)
        self.web_thread.start()
        # Give Flask a moment to start
        time.sleep(1)
        self.logger.info(f"Web UI started at http://127.0.0.1:{self.web_ui_port}")

# Global hub instance for Flask routes
hub_instance = None

# =============================================================================
# FLASK WEB UI ROUTES
# =============================================================================

@app.route('/')
def home():
    """Hub dashboard"""
    if not hub_instance:
        return "Hub not initialized", 500
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CREW CONTROL // HUB CONTROL</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-primary: #000a0e;
                --bg-secondary: #0a1419;
                --bg-tertiary: #0f1e27;
                --accent-cyan: #00fff7;
                --accent-green: #00ff7f;
                --accent-red: #ff004d;
                --accent-orange: #ff8b00;
                --accent-purple: #8a2be2;
                --text-primary: #ffffff;
                --text-secondary: #a0a9b8;
                --text-muted: #6c7683;
                --border-primary: rgba(0, 255, 247, 0.3);
                --border-secondary: rgba(160, 169, 184, 0.1);
                --glow-cyan: 0 0 20px rgba(0, 255, 247, 0.5);
                --glow-green: 0 0 20px rgba(0, 255, 127, 0.5);
                --glow-red: 0 0 20px rgba(255, 0, 77, 0.5);
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'JetBrains Mono', monospace;
                background: 
                    radial-gradient(circle at 20% 20%, rgba(0, 255, 247, 0.03) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(0, 255, 127, 0.02) 0%, transparent 50%),
                    linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
                min-height: 100vh;
                color: var(--text-primary);
                overflow-x: hidden;
                position: relative;
            }}
            
            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: 
                    linear-gradient(0deg, transparent 0%, rgba(0, 255, 247, 0.02) 50%, transparent 100%),
                    linear-gradient(90deg, transparent 0%, rgba(0, 255, 247, 0.01) 50%, transparent 100%);
                pointer-events: none;
                z-index: 1;
            }}
            
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 40px 20px;
                position: relative;
                z-index: 2;
            }}
            
            .system-header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 24px;
                background: rgba(15, 30, 39, 0.8);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border-primary);
                border-radius: 16px;
                box-shadow: var(--glow-cyan);
            }}
            
            .system-title {{
                font-size: 28px;
                font-weight: 700;
                color: var(--accent-cyan);
                text-transform: uppercase;
                letter-spacing: 3px;
                margin-bottom: 8px;
            }}
            
            .hub-info {{
                font-size: 16px;
                color: var(--text-secondary);
                font-weight: 500;
                letter-spacing: 1px;
            }}
            
            .status-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px; 
            }}
            
            .status-card {{
                text-align: center; 
                padding: 20px; 
                background: rgba(15, 30, 39, 0.6);
                backdrop-filter: blur(10px);
                border: 1px solid var(--border-primary);
                border-radius: 12px;
                transition: all 0.3s ease;
            }}
            
            .status-card:hover {{
                border-color: var(--accent-cyan);
                box-shadow: 0 0 20px rgba(0, 255, 247, 0.3);
                transform: translateY(-2px);
            }}
            
            .status-label {{
                font-size: 12px;
                font-weight: 600;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}
            
            .status-value {{
                font-size: 24px;
                font-weight: 700;
                color: var(--accent-cyan);
            }}
            
            .status-value.active {{
                color: var(--accent-green);
            }}
            
            .status-value.inactive {{
                color: var(--accent-red);
            }}
            
            .controls {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px; 
            }}
            
            .tech-btn {{
                background: linear-gradient(135deg, rgba(0, 255, 247, 0.1) 0%, rgba(0, 255, 127, 0.1) 100%);
                border: 1px solid var(--accent-cyan);
                color: var(--accent-cyan);
                padding: 16px 24px;
                border-radius: 12px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            
            .tech-btn::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 255, 247, 0.2), transparent);
                transition: left 0.5s ease;
            }}
            
            .tech-btn:hover::before {{
                left: 100%;
            }}
            
            .tech-btn:hover {{
                box-shadow: 0 0 25px rgba(0, 255, 247, 0.4);
                transform: translateY(-3px);
            }}
            
            .tech-btn.danger {{
                border-color: var(--accent-red);
                color: var(--accent-red);
                background: linear-gradient(135deg, rgba(255, 0, 77, 0.1) 0%, rgba(255, 0, 77, 0.05) 100%);
            }}
            
            .tech-btn.danger:hover {{
                box-shadow: 0 0 25px rgba(255, 0, 77, 0.4);
            }}
            
            .tech-btn.success {{
                border-color: var(--accent-green);
                color: var(--accent-green);
                background: linear-gradient(135deg, rgba(0, 255, 127, 0.1) 0%, rgba(0, 255, 127, 0.05) 100%);
            }}
            
            .tech-btn.success:hover {{
                box-shadow: 0 0 25px rgba(0, 255, 127, 0.4);
            }}
            
            .tech-btn.warning {{
                border-color: var(--accent-orange);
                color: var(--accent-orange);
                background: linear-gradient(135deg, rgba(255, 139, 0, 0.1) 0%, rgba(255, 139, 0, 0.05) 100%);
            }}
            
            .tech-btn.warning:hover {{
                box-shadow: 0 0 25px rgba(255, 139, 0, 0.4);
            }}
            
            .section {{
                margin-bottom: 40px;
            }}
            
            .section-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 1px solid var(--border-primary);
            }}
            
            .section-title {{
                font-size: 18px;
                font-weight: 700;
                color: var(--accent-cyan);
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            
            .section-count {{
                font-size: 12px;
                color: var(--text-muted);
                background: rgba(0, 255, 247, 0.1);
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid rgba(0, 255, 247, 0.3);
            }}
            
            .remote-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 16px;
            }}
            
            .remote-card {{
                padding: 20px;
                background: rgba(15, 30, 39, 0.6);
                border: 1px solid var(--border-secondary);
                border-radius: 12px;
                border-left: 4px solid var(--accent-green);
                transition: all 0.3s ease;
                position: relative;
            }}
            
            .remote-card:hover {{
                background: rgba(15, 30, 39, 0.8);
                transform: translateY(-2px);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }}
            
            .remote-name {{
                font-size: 16px;
                font-weight: 700;
                color: var(--text-primary);
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}
            
            .remote-command {{
                font-size: 14px;
                color: var(--accent-green);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}
            
            .remote-status {{
                position: absolute;
                top: 16px;
                right: 16px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 4px 8px;
                border-radius: 4px;
                background: rgba(0, 255, 127, 0.1);
                border: 1px solid var(--accent-green);
                color: var(--accent-green);
            }}
            
            .remote-time {{
                font-size: 12px;
                color: var(--text-muted);
                font-family: 'JetBrains Mono', monospace;
            }}
            
            .loading {{
                text-align: center;
                color: var(--text-muted);
                font-style: italic;
                padding: 40px;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="system-header">
                <div class="system-title">CREW CONTROL HUB</div>
                <div class="hub-info">{hub_instance.hub_name} ({hub_instance.hub_token})</div>
            </div>
            
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-label">Hub Status</div>
                    <div class="status-value" id="active">{hub_instance.hub_active and 'ACTIVE' or 'INACTIVE'}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Available Scripts</div>
                    <div class="status-value" id="scripts">{len(hub_instance.command_pool)}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Connected Remotes</div>
                    <div class="status-value" id="remotes">{len(hub_instance.paired_remotes)}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Auto-Timer</div>
                    <div class="status-value" id="timer">{'ON' if hub_instance.timer_enabled else 'OFF'}</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="tech-btn" onclick="toggleHub()">⚡ Toggle Hub</button>
                <button class="tech-btn success" onclick="shuffleAll()">🔀 Shuffle All</button>
                <button class="tech-btn warning" onclick="updateScripts()">📡 Update Scripts</button>
                <button class="tech-btn" onclick="cleanupRemotes()">🧹 Cleanup Remotes</button>
                <button class="tech-btn danger" onclick="shutdownHub()">🛑 Shutdown Hub</button>
            </div>
            
            <div class="section">
                <div class="section-header">
                    <div class="section-title">Connected Remotes</div>
                    <div class="section-count" id="remote-count">Loading...</div>
                </div>
                <div class="remote-grid" id="remote-list">
                    <div class="loading">Scanning for remotes...</div>
                </div>
            </div>
        </div>
        
        <script>
            function refreshStatus() {{
                fetch('/api/status')
                    .then(r => r.json())
                    .then(data => {{
                        // Update status values
                        const activeEl = document.getElementById('active');
                        activeEl.textContent = data.active ? 'ACTIVE' : 'INACTIVE';
                        activeEl.className = 'status-value ' + (data.active ? 'active' : 'inactive');
                        
                        document.getElementById('scripts').textContent = data.scripts;
                        document.getElementById('remotes').textContent = data.remotes;
                        document.getElementById('timer').textContent = data.timer ? 'ON' : 'OFF';
                        
                        // Update remote count
                        const remoteCountEl = document.getElementById('remote-count');
                        remoteCountEl.textContent = `${{data.remotes}} CONNECTED`;
                        
                        // Update remote list
                        const remoteList = document.getElementById('remote-list');
                        if (data.remote_list && data.remote_list.length > 0) {{
                            remoteList.innerHTML = data.remote_list.map(r => {{
                                const lastSeen = r.last_seen ? new Date(r.last_seen).toLocaleTimeString() : 'Unknown';
                                const displayName = r.username && r.username.trim() ? r.username : r.remote_id;
                                const timeSinceLastSeen = r.last_seen ? Date.now() - new Date(r.last_seen).getTime() : 999999;
                                const isOnline = timeSinceLastSeen < 120000; // 2 minutes
                                const statusClass = isOnline ? 'ONLINE' : 'OFFLINE';
                                const statusColor = isOnline ? 'var(--accent-green)' : 'var(--accent-red)';
                                
                                return `<div class="remote-card">
                                    <div class="remote-name">${{displayName}}</div>
                                    <div class="remote-command">${{r.assigned_command || 'No script assigned'}}</div>
                                    <div class="remote-time">Last seen: ${{lastSeen}}</div>
                                    <div class="remote-status" style="color: ${{statusColor}}; border-color: ${{statusColor}}; background: ${{statusColor}}10;">${{statusClass}}</div>
                                    <button class="tech-btn danger" style="position: absolute; bottom: 12px; right: 12px; padding: 4px 8px; font-size: 11px;" onclick="removeRemote('${{r.remote_id}}')">✕ REMOVE</button>
                                </div>`;
                            }}).join('');
                        }} else {{
                            remoteList.innerHTML = '<div class="loading">No remotes connected</div>';
                        }}
                    }})
                    .catch(e => console.error('Status error:', e));
            }}
            
            function toggleHub() {{
                fetch('/api/toggle-hub', {{method: 'POST'}})
                    .then(r => r.json())
                    .then(data => alert(data.message))
                    .then(() => refreshStatus());
            }}
            
            function shuffleAll() {{
                fetch('/api/shuffle', {{method: 'POST'}})
                    .then(r => r.json())
                    .then(data => alert(data.message))
                    .then(() => refreshStatus());
            }}
            
            function updateScripts() {{
                fetch('/api/update-scripts', {{method: 'POST'}})
                    .then(r => r.json())
                    .then(data => alert(data.message))
                    .then(() => refreshStatus());
            }}
            
            function cleanupRemotes() {{
                fetch('/api/cleanup', {{method: 'POST'}})
                    .then(r => r.json())
                    .then(data => {{
                        alert(data.message);
                        refreshStatus();
                    }});
            }}
            
            function removeRemote(remoteId) {{
                if (confirm(`Remove remote ${{remoteId}}?`)) {{
                    fetch('/api/remove-remote', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{remote_id: remoteId}})
                    }})
                    .then(r => r.json())
                    .then(data => {{
                        alert(data.message);
                        refreshStatus();
                    }});
                }}
            }}
            
            function shutdownHub() {{
                if (confirm('Are you sure you want to shutdown the hub?')) {{
                    fetch('/api/shutdown', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(data => alert(data.message));
                }}
            }}
            
            // Auto-refresh every 5 seconds
            setInterval(refreshStatus, 5000);
            refreshStatus();
        </script>
    </body>
    </html>
    """

@app.route('/api/status')
def get_hub_status():
    """Get hub status"""
    if not hub_instance:
        return jsonify({'error': 'Hub not initialized'}), 500
    
    # Auto-cleanup stale remotes
    hub_instance.cleanup_offline_remotes()
    
    remote_list = []
    for rid, rdata in hub_instance.paired_remotes.items():
        remote_list.append({
            'remote_id': rid,
            'username': rdata.get('username', ''),
            'assigned_command': rdata.get('assigned_command', ''),
            'last_seen': rdata.get('last_seen', '')
        })
    
    return jsonify({
        'active': hub_instance.hub_active,
        'scripts': len(hub_instance.command_pool),
        'remotes': len(hub_instance.paired_remotes),
        'timer': hub_instance.timer_enabled,
        'timer_minutes': hub_instance.timer_minutes,
        'remote_list': remote_list,
        'hub_name': hub_instance.hub_name,
        'hub_token': hub_instance.hub_token
    })

@app.route('/api/toggle-hub', methods=['POST'])
def toggle_hub():
    """Toggle hub active state"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    hub_instance.hub_active = not hub_instance.hub_active
    status = "activated" if hub_instance.hub_active else "deactivated"
    return jsonify({'success': True, 'message': f'Hub {status}'})

@app.route('/api/shuffle', methods=['POST'])
def shuffle_assignments():
    """Shuffle all remote assignments"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    try:
        success, message = hub_instance._shuffle_all_assignments()
        if success and hub_instance.nats_client:
            # Broadcast new assignments
            asyncio.run_coroutine_threadsafe(
                hub_instance._broadcast_assignments(),
                asyncio.get_event_loop()
            )
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'})

@app.route('/api/update-scripts', methods=['POST'])
def update_scripts():
    """Update scripts from git"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    try:
        success, message = hub_instance.update_scripts_from_git()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_remotes():
    """Manually cleanup offline remotes"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    try:
        before_count = len(hub_instance.paired_remotes)
        hub_instance.cleanup_offline_remotes()
        after_count = len(hub_instance.paired_remotes)
        removed_count = before_count - after_count
        
        if removed_count > 0:
            message = f'Removed {removed_count} offline remote(s)'
        else:
            message = 'No offline remotes to remove'
            
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'})

@app.route('/api/remove-remote', methods=['POST'])
def remove_remote():
    """Manually remove a specific remote"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    try:
        data = request.get_json()
        remote_id = data.get('remote_id')
        
        if not remote_id:
            return jsonify({'success': False, 'message': 'Remote ID required'})
        
        if remote_id in hub_instance.paired_remotes:
            del hub_instance.paired_remotes[remote_id]
            hub_instance.save_paired_remotes()
            hub_instance._ensure_unique_assignments()
            hub_instance.logger.info(f"Manually removed remote: {remote_id}")
            return jsonify({'success': True, 'message': f'Removed remote {remote_id}'})
        else:
            return jsonify({'success': False, 'message': 'Remote not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'})

@app.route('/api/shutdown', methods=['POST'])
def shutdown_hub():
    """Shutdown the hub"""
    if not hub_instance:
        return jsonify({'success': False, 'message': 'Hub not initialized'}), 500
    
    try:
        hub_instance.shutdown_requested = True
        hub_instance.logger.info("Shutdown requested via web UI")
        return jsonify({'success': True, 'message': 'Hub shutdown initiated'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'})

def main():
    global hub_instance
    
    # Single instance check using Windows mutex
    import ctypes
    import sys
    
    mutex_name = "Global\\P_Buttons_Hub_Mutex_x7k9m"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, True, mutex_name)
    
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        # Hub is already running
        sys.exit(0)
    
    try:
        hub_instance = AutomationHub()
        asyncio.run(hub_instance.run())
    except Exception as e:
        logging.error(f"Hub error: {e}")
    finally:
        if mutex:
            kernel32.CloseHandle(mutex)

if __name__ == "__main__":
    main()
