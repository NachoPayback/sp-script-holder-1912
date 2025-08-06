#!/usr/bin/env python3
"""
Displays authentic Windows toast notifications
"""

import random
import subprocess


def show_system_notification():
    """Show a Windows 10/11 toast notification that looks completely authentic"""

    # List of authentic system notification messages
    notifications = [
        {
            "title": "System",
            "message": "Your computer will restart in 30 seconds to install important updates",
            "app": "Windows Update"
        },
        {
            "title": "System", 
            "message": "Your system is running low on memory. Consider closing some applications",
            "app": "Windows Security"
        },
        {
            "title": "Hardware",
            "message": "New USB device detected. Installing device drivers...",
            "app": "Device Manager"
        },
        {
            "title": "Windows Security",
            "message": "Quick scan completed. Your device is protected",
            "app": "Windows Defender Antivirus"
        },
        {
            "title": "Windows Security", 
            "message": "Minor threat detected, consider investigating!",
            "app": "Windows Defender Antivirus"
        },
        {
            "title": "Network",
            "message": "Connected to secure network", 
            "app": "Network & Internet"
        }
    ]

    try:
        # Pick a random notification
        notif = random.choice(notifications)

        # Use modern Windows notification with TaskDialog API
        ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName PresentationFramework

# Try modern TaskDialog first (Windows 10/11 style)
try {{
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;

    public class TaskDialog {{
        [DllImport("comctl32.dll", CharSet = CharSet.Unicode)]
        public static extern int TaskDialog(IntPtr hwndParent, IntPtr hInstance, 
            string pszWindowTitle, string pszMainInstruction, string pszContent, 
            int dwCommonButtons, IntPtr pszIcon, out int pnButton);
    }}
"@

    $result = 0
    [TaskDialog]::TaskDialog([System.IntPtr]::Zero, [System.IntPtr]::Zero, 
        "{notif['app']}", "{notif['title']}", "{notif['message']}", 
        1, [System.IntPtr]::Zero, [ref]$result)
}} catch {{
    # Fallback to styled MessageBox
    [System.Windows.Forms.MessageBox]::Show("{notif['message']}", "{notif['title']}", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
}}
'''

        # Execute PowerShell script to show native toast
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script
        ], capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)

        return result.returncode == 0

    except Exception:
        return False

if __name__ == "__main__":
    show_system_notification()
