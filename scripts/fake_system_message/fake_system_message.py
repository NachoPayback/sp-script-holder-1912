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

        # Create a visible message box that looks like a system notification
        ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create a custom notification window
$form = New-Object System.Windows.Forms.Form
$form.Text = "{notif['app']}"
$form.Size = New-Object System.Drawing.Size(400, 120)
$form.StartPosition = "Manual"
$form.Location = New-Object System.Drawing.Point(([System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width - 400), 50)
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = [System.Drawing.Color]::White

# Add title label
$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "{notif['title']}"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$titleLabel.Location = New-Object System.Drawing.Point(10, 10)
$titleLabel.Size = New-Object System.Drawing.Size(370, 25)
$form.Controls.Add($titleLabel)

# Add message label
$messageLabel = New-Object System.Windows.Forms.Label
$messageLabel.Text = "{notif['message']}"
$messageLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$messageLabel.Location = New-Object System.Drawing.Point(10, 35)
$messageLabel.Size = New-Object System.Drawing.Size(370, 40)
$messageLabel.AutoSize = $false
$form.Controls.Add($messageLabel)

# Auto-close timer
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 4000
$timer.Add_Tick({{ $form.Close() }})
$timer.Start()

# Show the form
$form.ShowDialog() | Out-Null
'''

        # Execute PowerShell script to show native notification
        result = subprocess.run([
            "powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-Command", ps_script
        ], capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            print(f"Successfully displayed balloon notification: {notif['title']} - {notif['message']}")
            return True
        else:
            # If PowerShell fails, show error message and fallback
            print(f"PowerShell notification failed. Return code: {result.returncode}")
            if result.stderr:
                print(f"PowerShell stderr: {result.stderr}")
            if result.stdout:
                print(f"PowerShell stdout: {result.stdout}")

            # Fallback: just print to console as a basic notification
            print(f"[NOTIFICATION] {notif['title']}: {notif['message']}")
            return True

    except subprocess.TimeoutExpired:
        print("Notification timeout")
        return False
    except Exception as e:
        print(f"Error showing notification: {e}")
        return False

if __name__ == "__main__":
    show_system_notification()
