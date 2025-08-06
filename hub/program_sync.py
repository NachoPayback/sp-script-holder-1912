#!/usr/bin/env python3
"""
Program Sync Module for SP Crew Hub
Handles smart sync of executables from GitHub dist/programs folder
"""

import os
import json
import shutil
import tempfile
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests


class ProgramSync:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.local_programs_dir = Path.home() / "SP-Crew-Hub" / "programs"
        self.cache_file = Path.home() / "SP-Crew-Hub" / "sync_cache.json"
        self.repo_url = "https://github.com/NachoPayback/sp-script-holder-1912"
        self.programs_api_url = "https://api.github.com/repos/NachoPayback/sp-script-holder-1912/contents/dist/programs"
        
    def ensure_local_directory(self):
        """Ensure local programs directory exists"""
        self.local_programs_dir.mkdir(parents=True, exist_ok=True)
        
    def get_github_programs(self) -> Dict[str, Dict]:
        """Get list of programs from GitHub API"""
        try:
            response = requests.get(self.programs_api_url, timeout=10)
            response.raise_for_status()
            
            programs = {}
            for item in response.json():
                if item['type'] == 'file' and item['name'].endswith('.exe'):
                    programs[item['name']] = {
                        'sha': item['sha'],
                        'size': item['size'],
                        'download_url': item['download_url']
                    }
            
            return programs
            
        except Exception as e:
            self.logger.error(f"Failed to get GitHub programs list: {e}")
            return {}
    
    def get_local_programs(self) -> Dict[str, Dict]:
        """Get list of local programs with metadata"""
        programs = {}
        
        if not self.local_programs_dir.exists():
            return programs
            
        for exe_file in self.local_programs_dir.glob("*.exe"):
            # Calculate file hash for comparison
            try:
                with open(exe_file, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.sha1(content).hexdigest()
                    
                programs[exe_file.name] = {
                    'sha': file_hash,
                    'size': exe_file.stat().st_size,
                    'path': exe_file
                }
            except Exception as e:
                self.logger.warning(f"Could not read local program {exe_file.name}: {e}")
                
        return programs
    
    def load_cache(self) -> Dict:
        """Load sync cache"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load cache: {e}")
        return {}
    
    def save_cache(self, cache_data: Dict):
        """Save sync cache"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save cache: {e}")
    
    def download_program(self, name: str, download_url: str) -> bool:
        """Download a program from GitHub"""
        try:
            self.logger.info(f"Downloading {name}...")
            
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            exe_path = self.local_programs_dir / name
            with open(exe_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded {name} ({len(response.content) // 1024} KB)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {name}: {e}")
            return False
    
    def sync_programs(self) -> bool:
        """Smart sync programs from GitHub"""
        try:
            self.logger.info("Checking for program updates...")
            
            self.ensure_local_directory()
            
            # Get current state
            github_programs = self.get_github_programs()
            local_programs = self.get_local_programs()
            cache = self.load_cache()
            
            if not github_programs:
                self.logger.warning("No programs found on GitHub")
                return False
            
            changes = 0
            
            # DELETE removed programs
            for local_name in list(local_programs.keys()):
                if local_name not in github_programs:
                    local_path = local_programs[local_name]['path']
                    local_path.unlink()
                    self.logger.info(f"DELETED: {local_name}")
                    changes += 1
            
            # ADD new programs and UPDATE changed ones
            for github_name, github_info in github_programs.items():
                local_info = local_programs.get(github_name)
                cached_info = cache.get('programs', {}).get(github_name, {})
                
                needs_download = False
                
                if not local_info:
                    # New program
                    needs_download = True
                    action = "ADD"
                elif github_info['sha'] != cached_info.get('sha'):
                    # Program updated on GitHub
                    needs_download = True  
                    action = "UPDATE"
                elif github_info['size'] != local_info['size']:
                    # Size mismatch
                    needs_download = True
                    action = "REPAIR"
                
                if needs_download:
                    if self.download_program(github_name, github_info['download_url']):
                        self.logger.info(f"{action}: {github_name}")
                        changes += 1
            
            # Update cache
            cache_data = {
                'last_sync': datetime.now().isoformat(),
                'programs': github_programs
            }
            self.save_cache(cache_data)
            
            if changes > 0:
                self.logger.info(f"Sync complete: {changes} changes made")
            else:
                self.logger.info("Programs are up to date")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Program sync failed: {e}")
            return False
    
    def get_available_programs(self) -> List[str]:
        """Get list of available programs"""
        if not self.local_programs_dir.exists():
            return []
            
        programs = []
        for exe_file in self.local_programs_dir.glob("*.exe"):
            # Convert filename to script name (remove .exe)
            script_name = exe_file.stem
            programs.append(script_name)
            
        return sorted(programs)
    
    def execute_program(self, program_name: str) -> Dict:
        """Execute a program"""
        exe_path = self.local_programs_dir / f"{program_name}.exe"
        
        if not exe_path.exists():
            return {
                "success": False,
                "error": f"Program not found: {program_name}",
                "duration_ms": 0
            }
        
        try:
            import subprocess
            import time
            
            start_time = time.time()
            
            # Execute the program with no window
            result = subprocess.run(
                [str(exe_path)],
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
                "error": "Program execution timed out (30s)",
                "duration_ms": 30000
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration_ms": 0
            }