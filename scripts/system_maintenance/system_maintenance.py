#!/usr/bin/env python3
"""
Shows authentic Windows 10/11 toast notifications for system maintenance
"""

import random
import subprocess
import time

def trigger_windows_toast():
    """Show real Windows toast notifications using native Windows APIs"""
    
    # List of system maintenance toast messages
    maintenance_toasts = [
        {
            "title": "System Maintenance",
            "message": "Running scheduled system cleanup... This may take a few minutes.",
            "icon": "⚙️"
        },
        {
            "title": "Disk Cleanup",
            "message": "Clearing temporary files and optimizing storage space.",
            "icon": "💾"
        },
        {
            "title": "System Optimization", 
            "message": "Defragmenting drives and optimizing performance.",
            "icon": "🚀"
        },
        {
            "title": "Registry Cleanup",
            "message": "Scanning and repairing registry entries.",
            "icon": "🔧"
        },
        {
            "title": "Update Check",
            "message": "Checking for critical system updates.",
            "icon": "🔄"
        },
        {
            "title": "Memory Optimization",
            "message": "Clearing system cache and optimizing memory usage.",
            "icon": "💻"
        }
    ]
    
    try:
        # Pick a random maintenance message
        toast = random.choice(maintenance_toasts)
        
        # Create PowerShell script for BurntToast module
        ps_script = '''
# Install BurntToast if not already installed
if (!(Get-Module -ListAvailable -Name BurntToast)) {
    Install-Module -Name BurntToast -Force -Scope CurrentUser
}
Import-Module BurntToast -Force

# Show the toast notification
New-BurntToastNotification -Text "''' + toast['title'] + '''", "''' + toast['message'] + '''" -AppLogo "C:\\Windows\\System32\\UserAccountControlSettings.exe"
'''
        
        # Try BurntToast first
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            # Fallback to simple notification
            print("BurntToast failed, using fallback notification method...")
            
            # Use Windows MSG command as fallback
            msg_command = f'msg * /TIME:10 "{toast["title"]}\\n\\n{toast["message"]}"'
            subprocess.run(msg_command, shell=True, capture_output=True)
            
            # Also try Windows 10 toast via PowerShell without dependencies
            simple_ps = f'''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipIcon = "Info"
$notification.BalloonTipTitle = "{toast['title']}"
$notification.BalloonTipText = "{toast['message']}"
$notification.Visible = $true
$notification.ShowBalloonTip(10000)
Start-Sleep -Seconds 10
$notification.Dispose()
'''
            subprocess.run([
                "powershell", "-ExecutionPolicy", "Bypass", "-Command", simple_ps
            ], capture_output=True, text=True, timeout=15)
        
        print(f"Displayed notification: {toast['title']} - {toast['message']}")
        
        # Show follow-up notification after delay
        time.sleep(3)
        
        follow_up_ps = '''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipIcon = "Info"
$notification.BalloonTipTitle = "Maintenance Complete"
$notification.BalloonTipText = "System maintenance tasks completed successfully."
$notification.Visible = $true
$notification.ShowBalloonTip(5000)
Start-Sleep -Seconds 5
$notification.Dispose()
'''
        
        subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-Command", follow_up_ps
        ], capture_output=True, text=True, timeout=10)
        
        return True
            
    except subprocess.TimeoutExpired:
        print("Notification timeout")
        return False
    except Exception as e:
        print(f"Error showing notification: {e}")
        return False

if __name__ == "__main__":
    trigger_windows_toast()