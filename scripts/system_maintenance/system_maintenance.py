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
            "app": "Windows System"
        },
        {
            "title": "Disk Cleanup",
            "message": "Clearing temporary files and optimizing storage space.",
            "app": "Storage Sense"
        },
        {
            "title": "System Optimization",
            "message": "Defragmenting drives and optimizing performance.",
            "app": "Windows Maintenance"
        },
        {
            "title": "Registry Cleanup",
            "message": "Scanning and repairing registry entries.",
            "app": "System Tools"
        },
        {
            "title": "Update Check",
            "message": "Checking for critical system updates.",
            "app": "Windows Update"
        },
        {
            "title": "Memory Optimization",
            "message": "Clearing system cache and optimizing memory usage.",
            "app": "Task Manager"
        }
    ]
    
    try:
        # Pick a random maintenance message
        toast = random.choice(maintenance_toasts)
        
        # Use Windows' built-in toast notification system via PowerShell
        ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{toast['title']}</text>
            <text>{toast['message']}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Default" />
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = "SystemMaintenance"
$toast.Group = "System"

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{toast['app']}")
$notifier.Show($toast)
'''
        
        # Execute PowerShell script for real Windows toast
        result = subprocess.run([
            "powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_script
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"Successfully displayed Windows toast: {toast['title']} - {toast['message']}")
            
            # Show a second toast after a delay for more impact
            time.sleep(2)
            
            follow_up = {
                "title": "Maintenance Complete",
                "message": "System maintenance tasks completed successfully.",
                "app": "Windows System"
            }
            
            ps_script2 = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{follow_up['title']}</text>
            <text>{follow_up['message']}</text>
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.Looping.Alarm" />
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = "MaintenanceComplete"
$toast.Group = "System"

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{follow_up['app']}")
$notifier.Show($toast)
'''
            
            subprocess.run([
                "powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_script2
            ], capture_output=True, text=True, timeout=10)
            
            return True
        else:
            print(f"Toast notification failed. Return code: {result.returncode}")
            if result.stderr:
                print(f"PowerShell stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Toast notification timeout")
        return False
    except Exception as e:
        print(f"Error showing toast notification: {e}")
        return False

if __name__ == "__main__":
    trigger_windows_toast()