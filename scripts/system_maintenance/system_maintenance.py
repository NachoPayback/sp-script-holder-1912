#!/usr/bin/env python3
"""
Shows native Windows notifications for fake system maintenance
"""

import random
import subprocess
import sys


def show_windows_notification():
    """Show native Windows notification using plyer library"""
    
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
        },
        {
            "title": "Data Protection Active", 
            "message": "Encrypting sensitive files due to security threat detected."
        },
        {
            "title": "System Lockdown",
            "message": "High-risk activity detected. Initiating protective measures."
        },
        {
            "title": "Emergency Backup",
            "message": "Creating emergency system backup due to potential data loss risk."
        },
        {
            "title": "Network Isolation",
            "message": "Suspicious connections terminated. System running in safe mode."
        }
    ]
    
    try:
        # Try using plyer first (most reliable)
        from plyer import notification
        
        # Pick random message
        msg = random.choice(maintenance_messages)
        
        # Show notification
        notification.notify(
            title=msg["title"],
            message=msg["message"],
            app_name="Windows Security",
            app_icon=None,
            timeout=8
        )
        
        return True
        
    except ImportError:
        # Install plyer if not available
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "plyer"])
            from plyer import notification
            
            msg = random.choice(maintenance_messages)
            notification.notify(
                title=msg["title"],
                message=msg["message"],
                app_name="Windows Security",
                app_icon=None,
                timeout=8
            )
            return True
            
        except Exception:
            # Final fallback - PowerShell balloon tip
            msg = random.choice(maintenance_messages)
            
            ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notification = New-Object System.Windows.Forms.NotifyIcon
$notification.Icon = [System.Drawing.SystemIcons]::Information
$notification.BalloonTipIcon = "Info"
$notification.BalloonTipTitle = "{msg['title']}"
$notification.BalloonTipText = "{msg['message']}"
$notification.Visible = $true
$notification.ShowBalloonTip(8000)
Start-Sleep -Seconds 8
$notification.Dispose()
'''
            
            try:
                subprocess.run([
                    "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script
                ], capture_output=True, text=True, timeout=15)
                return True
            except Exception:
                return False
    
    except Exception:
        return False


def main():
    """Main function"""
    try:
        # Hide console on Windows
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        
        show_windows_notification()
        
    except:
        pass


if __name__ == "__main__":
    main()