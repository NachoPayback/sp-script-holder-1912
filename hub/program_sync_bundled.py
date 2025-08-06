#!/usr/bin/env python3
"""
Program Sync Module for SP Crew Hub - Bundled Scripts Version
Downloads and manages a single scripts.exe package instead of individual executables
"""

import os
import json
import shutil
import tempfile
import hashlib
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests


class ProgramSync:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.local_programs_dir = Path.home() / "SP-Crew-Hub" / "programs"
        self.scripts_exe_path = self.local_programs_dir / "scripts.exe"
        self.version_file = self.local_programs_dir / "version.json"
        self.repo_url = "https://github.com/NachoPayback/sp-script-holder-1912"
        self.version_api_url = "https://api.github.com/repos/NachoPayback/sp-script-holder-1912/contents/dist/version.json"
        self.scripts_api_url = "https://api.github.com/repos/NachoPayback/sp-script-holder-1912/contents/dist/scripts.exe"
        
    def ensure_local_directory(self):
        """Ensure local programs directory exists"""
        self.local_programs_dir.mkdir(parents=True, exist_ok=True)
        
    def get_github_version(self) -> Optional[Dict]:
        """Get version info from GitHub"""
        try:
            response = requests.get(self.version_api_url, timeout=10)
            response.raise_for_status()
            
            # Decode base64 content
            import base64
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return json.loads(content)
            
        except Exception as e:
            self.logger.error(f"Failed to get GitHub version: {e}")
            return None
    
    def get_local_version(self) -> Optional[Dict]:
        """Get local version info"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not read local version: {e}")
        return None
    
    def download_scripts_package(self) -> bool:
        """Download the scripts.exe package from GitHub"""
        try:
            self.logger.info("Downloading scripts package...")
            
            # Get download URL
            response = requests.get(self.scripts_api_url, timeout=10)
            response.raise_for_status()
            download_url = response.json()['download_url']
            
            # Download file
            self.logger.info("Downloading scripts.exe (this may take a moment)...")
            response = requests.get(download_url, timeout=120, stream=True)
            response.raise_for_status()
            
            # Save to temp file first
            temp_path = self.scripts_exe_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Move to final location
            if self.scripts_exe_path.exists():
                self.scripts_exe_path.unlink()
            temp_path.rename(self.scripts_exe_path)
            
            # Get and save version info
            github_version = self.get_github_version()
            if github_version:
                with open(self.version_file, 'w') as f:
                    json.dump(github_version, f, indent=2)
            
            size_mb = self.scripts_exe_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"Downloaded scripts.exe ({size_mb:.1f} MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download scripts package: {e}")
            return False
    
    def sync_programs(self) -> bool:
        """Smart sync scripts package from GitHub"""
        try:
            self.logger.info("Checking for script updates...")
            
            self.ensure_local_directory()
            
            # Get version info
            github_version = self.get_github_version()
            local_version = self.get_local_version()
            
            if not github_version:
                self.logger.warning("Could not get GitHub version info")
                return False
            
            # Check if update needed
            needs_update = False
            
            if not local_version or not self.scripts_exe_path.exists():
                needs_update = True
                self.logger.info("No local scripts found, downloading...")
            elif github_version['version'] != local_version.get('version'):
                needs_update = True
                self.logger.info(f"Update available: {local_version['version']} -> {github_version['version']}")
            elif github_version['hash'] != local_version.get('hash'):
                needs_update = True
                self.logger.info("Scripts package has changed, updating...")
            
            if needs_update:
                if self.download_scripts_package():
                    self.logger.info("Scripts updated successfully")
                    return True
                else:
                    return False
            else:
                self.logger.info("Scripts are up to date")
                return True
                
        except Exception as e:
            self.logger.error(f"Scripts sync failed: {e}")
            return False
    
    def get_available_programs(self) -> List[str]:
        """Get list of available scripts from the package"""
        if not self.scripts_exe_path.exists():
            return []
            
        try:
            # Run scripts.exe --list to get available scripts
            result = subprocess.run(
                [str(self.scripts_exe_path), "--list"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # Parse output to get script names
                scripts = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        script_name = line[2:].strip()
                        scripts.append(script_name)
                return sorted(scripts)
            else:
                self.logger.error(f"Failed to list scripts: {result.stderr}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting available scripts: {e}")
            return []
    
    def execute_program(self, program_name: str) -> Dict:
        """Execute a script from the package"""
        if not self.scripts_exe_path.exists():
            return {
                "success": False,
                "error": "Scripts package not found",
                "duration_ms": 0
            }
        
        try:
            import time
            
            start_time = time.time()
            
            # Execute the script via scripts.exe
            result = subprocess.run(
                [str(self.scripts_exe_path), "--run", program_name],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "duration_ms": duration_ms,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Script execution timed out (30s)",
                "duration_ms": 30000
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": 0
            }
    
    def spawn_program(self, program_name: str) -> subprocess.Popen:
        """Spawn a script without waiting for it to complete"""
        if not self.scripts_exe_path.exists():
            raise FileNotFoundError("Scripts package not found")
        
        # Spawn the process without waiting
        process = subprocess.Popen(
            [str(self.scripts_exe_path), "--run", program_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        return process