#!/usr/bin/env python3
"""
Shows native Windows notifications for fake system maintenance
"""

import random
import subprocess
import sys


def main():
    """Main function"""
    try:
        maintenance_messages = [
            {
                "title": "Security Alert",
                "message": "Suspicious network activity detected. Running emergency scan..."
            },
            {
                "title": "System Compromise Detected", 
                "message": "Unauthorized access attempt blocked. Securing system files."
            },
            {
                "title": "Critical Security Update",
                "message": "Installing emergency security patches. Do not restart computer."
            },
            {
                "title": "Virus Quarantine",
                "message": "Malicious files detected and quarantined. System cleanup in progress."
            },
            {
                "title": "Firewall Breach Alert",
                "message": "External intrusion blocked. Reinforcing security protocols."
            }
        ]
        
        # Pick random message
        msg = random.choice(maintenance_messages)
        
        # Use PowerShell to show Windows toast notification
        powershell_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Warning
$notification.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Warning
$notification.BalloonTipText = "{msg["message"]}"
$notification.BalloonTipTitle = "{msg["title"]}"
$notification.Visible = $true
$notification.ShowBalloonTip(8000)
Start-Sleep 9
$notification.Dispose()
'''
        
        subprocess.run(["powershell", "-Command", powershell_script], 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
    except:
        pass


if __name__ == "__main__":
    main()