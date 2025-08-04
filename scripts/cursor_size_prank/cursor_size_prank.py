#!/usr/bin/env python3
"""
Cursor Size Chaos - Changes Windows cursor size using multiple methods
"""

import time
import subprocess
import sys

try:
    import ctypes
    import winreg
except ImportError:
    print("This script requires Windows")
    exit(1)


def set_cursor_size_powershell(size):
    """Use PowerShell to change cursor size via Windows Settings API"""
    print(f"Setting cursor size to {size} using PowerShell method...")
    
    ps_script = f'''
try {{
    # Load required assemblies
    Add-Type -AssemblyName System.Windows.Forms
    
    # Ensure registry paths exist
    $accessibilityPath = "HKCU:\\Software\\Microsoft\\Accessibility"
    if (-not (Test-Path $accessibilityPath)) {{
        New-Item -Path $accessibilityPath -Force | Out-Null
    }}
    
    $cursorPath = "HKCU:\\Control Panel\\Cursors"
    if (-not (Test-Path $cursorPath)) {{
        New-Item -Path $cursorPath -Force | Out-Null
    }}
    
    # Set cursor size values
    Set-ItemProperty -Path $accessibilityPath -Name "CursorSize" -Value {size} -Force
    
    # Calculate and set base size
    $baseSize = 32 + ({size} - 1) * 16
    Set-ItemProperty -Path $cursorPath -Name "CursorBaseSize" -Value $baseSize -Force
    
    # Define Windows API functions
    Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class WinAPI {{
            [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
            public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, IntPtr pvParam, uint fWinIni);
            
            [DllImport("user32.dll", CharSet = CharSet.Auto)]
            public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
            
            [DllImport("user32.dll")]
            public static extern IntPtr GetDesktopWindow();
            
            [DllImport("user32.dll")]
            public static extern bool InvalidateRect(IntPtr hWnd, IntPtr lpRect, bool bErase);
            
            [DllImport("user32.dll")]
            public static extern bool UpdateWindow(IntPtr hWnd);
        }}
"@
    
    # Constants
    $SPI_SETCURSORS = 0x0057
    $SPI_SETMOUSETRAILS = 0x0071  
    $SPIF_UPDATEINIFILE = 0x01
    $SPIF_SENDCHANGE = 0x02
    $WM_SETTINGCHANGE = 0x001A
    $HWND_BROADCAST = [IntPtr]0xFFFF
    
    # Apply changes using multiple Windows API calls
    Write-Host "Applying cursor changes..."
    
    # Method 1: SystemParametersInfo calls
    [WinAPI]::SystemParametersInfo($SPI_SETCURSORS, 0, [IntPtr]::Zero, $SPIF_UPDATEINIFILE -bor $SPIF_SENDCHANGE) | Out-Null
    [WinAPI]::SystemParametersInfo($SPI_SETMOUSETRAILS, 0, [IntPtr]::Zero, $SPIF_UPDATEINIFILE -bor $SPIF_SENDCHANGE) | Out-Null
    
    # Method 2: Broadcast setting change message
    [WinAPI]::SendMessage($HWND_BROADCAST, $WM_SETTINGCHANGE, [IntPtr]0, [IntPtr]0) | Out-Null
    
    # Method 3: Force desktop refresh
    $desktop = [WinAPI]::GetDesktopWindow()
    [WinAPI]::InvalidateRect($desktop, [IntPtr]::Zero, $true) | Out-Null
    [WinAPI]::UpdateWindow($desktop) | Out-Null
    
    # Method 4: Trigger accessibility settings refresh
    try {{
        # Access mouse settings to trigger internal refresh
        $mouseSpeed = (Get-ItemProperty -Path "HKCU:\\Control Panel\\Mouse" -Name "MouseSensitivity" -ErrorAction SilentlyContinue).MouseSensitivity
        if ($mouseSpeed) {{
            Set-ItemProperty -Path "HKCU:\\Control Panel\\Mouse" -Name "MouseSensitivity" -Value $mouseSpeed -Force
            [WinAPI]::SystemParametersInfo(0x0003, 0, [IntPtr]::Zero, $SPIF_UPDATEINIFILE -bor $SPIF_SENDCHANGE) | Out-Null
        }}
    }} catch {{
        # Ignore errors in this optional step
    }}
    
    Write-Host "Cursor size change completed successfully!"
    Write-Host "Base size set to: $baseSize pixels"
    Write-Host "Registry values updated for size level: {size}"
    
}} catch {{
    Write-Host "Error in PowerShell method: $($_.Exception.Message)"
    exit 1
}}
'''
    
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        print("PowerShell output:", result.stdout)
        if result.stderr:
            print("PowerShell errors:", result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("PowerShell method timed out")
        return False
    except Exception as e:
        print(f"PowerShell method failed: {e}")
        return False


def set_cursor_size_registry(size):
    """Fallback method using Python registry access"""
    print(f"Setting cursor size to {size} using registry method...")
    
    try:
        # Create/update Accessibility registry entry
        acc_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Accessibility")
        winreg.SetValueEx(acc_key, "CursorSize", 0, winreg.REG_DWORD, size)
        winreg.CloseKey(acc_key)
        print("✓ Accessibility registry updated")
        
        # Calculate and set cursor base size
        base_size = 32 + (size - 1) * 16
        cursor_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Cursors")
        winreg.SetValueEx(cursor_key, "CursorBaseSize", 0, winreg.REG_DWORD, base_size)
        winreg.CloseKey(cursor_key)
        print(f"✓ Cursor base size set to {base_size}px")
        
        # Force Windows to apply changes
        SPI_SETCURSORS = 0x0057
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        
        success = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETCURSORS, 0, None, SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        if success:
            print("✓ System notified of cursor changes")
        else:
            print("⚠ System notification may have failed")
            
        return True
        
    except Exception as e:
        print(f"Registry method failed: {e}")
        return False


def get_current_cursor_size():
    """Get current cursor size from registry"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Accessibility", 0, winreg.KEY_READ)
        try:
            cursor_size, _ = winreg.QueryValueEx(key, "CursorSize")
            winreg.CloseKey(key)
            return cursor_size
        except FileNotFoundError:
            winreg.CloseKey(key)
            return 1  # Default size
    except Exception:
        return 1  # Default if we can't read


def force_cursor_refresh():
    """Try additional methods to force cursor refresh"""
    print("Attempting additional cursor refresh methods...")
    
    try:
        # Method 1: Toggle mouse trails to force refresh
        ps_script = '''
        try {
            Add-Type @"
                using System;
                using System.Runtime.InteropServices;
                public class MouseAPI {
                    [DllImport("user32.dll")]
                    public static extern bool SystemParametersInfo(uint uiAction, uint uiParam, IntPtr pvParam, uint fWinIni);
                }
"@
            # Toggle mouse trails off and on to refresh cursor
            [MouseAPI]::SystemParametersInfo(0x0016, 0, [IntPtr]::Zero, 0x03)  # SPI_SETMOUSETRAILS off
            Start-Sleep -Milliseconds 100
            [MouseAPI]::SystemParametersInfo(0x0016, 1, [IntPtr]::Zero, 0x03)  # SPI_SETMOUSETRAILS on
            Start-Sleep -Milliseconds 100  
            [MouseAPI]::SystemParametersInfo(0x0016, 0, [IntPtr]::Zero, 0x03)  # SPI_SETMOUSETRAILS off again
            
            Write-Host "Mouse trails toggle complete"
        } catch {
            Write-Host "Mouse trails toggle failed: $($_.Exception.Message)"
        }
        '''
        
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            timeout=5
        )
        print("✓ Mouse trails refresh attempted")
        
    except Exception as e:
        print(f"Additional refresh methods failed: {e}")


def main():
    """Main cursor size change function"""
    print("=" * 50)
    print("CURSOR SIZE CHAOS - Advanced Windows Cursor Modification")
    print("=" * 50)
    
    # Check for reset command
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("RESET MODE: Restoring cursor to default size...")
        
        success = False
        if set_cursor_size_powershell(1):
            success = True
        elif set_cursor_size_registry(1):
            success = True
            
        if success:
            print("✅ Cursor reset to default size!")
        else:
            print("❌ Reset failed - try manually in Settings > Accessibility > Mouse pointer")
        return
    
    # Get current cursor size
    original_size = get_current_cursor_size()
    print(f"📍 Current cursor size: {original_size}")
    
    # Set to giant cursor (size 10 = very large)
    target_size = 10
    print(f"🎯 Target cursor size: {target_size}")
    print()
    
    print("Starting cursor size modification...")
    success = False
    
    # Try PowerShell method first (most reliable)
    if set_cursor_size_powershell(target_size):
        success = True
        print("✅ PowerShell method succeeded!")
    else:
        print("❌ PowerShell method failed, trying registry method...")
        
        # Try registry method as fallback
        if set_cursor_size_registry(target_size):
            success = True
            print("✅ Registry method succeeded!")
        else:
            print("❌ Registry method also failed")
    
    if success:
        # Try additional refresh methods
        force_cursor_refresh()
        
        print()
        print("🎉 CURSOR SIZE CHANGE COMPLETE!")
        print("📋 To see the change:")
        print("   1. Move your mouse cursor around")
        print("   2. If no change, try pressing Win+L to lock/unlock screen")
        print("   3. Or restart applications/reboot if needed")
        print()
        print("⏰ Cursor will be restored to normal size in 15 seconds...")
        
        # Wait before restoring
        for i in range(15, 0, -1):
            print(f"   Restoring in {i} seconds...", end="\r")
            time.sleep(1)
        print()
        
        # Restore original size
        print("🔄 Restoring original cursor size...")
        if set_cursor_size_powershell(original_size) or set_cursor_size_registry(original_size):
            print("✅ Cursor restored to original size!")
        else:
            print("⚠ Could not restore automatically. Manual reset may be needed.")
            print("   Go to Settings > Accessibility > Mouse pointer to adjust manually")
            
    else:
        print()
        print("❌ FAILED TO CHANGE CURSOR SIZE")
        print("💡 This could be due to:")
        print("   • Windows permissions/UAC restrictions")
        print("   • System policy preventing cursor changes")
        print("   • Need to run as administrator")
        print("   • Try manually: Settings > Accessibility > Mouse pointer")
    
    print()
    print("🏁 Cursor size chaos complete!")


if __name__ == "__main__":
    main()