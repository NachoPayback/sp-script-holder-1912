#!/usr/bin/env python3
"""
Rick Roll Prank - Plays local MP4 video file
"""

import time
import random
import subprocess
from pathlib import Path

def main():
    """Main Rick Roll prank function"""
    print("Rick Roll Prank - Local Video")
    print("=" * 40)
    
    # Random duration between 3-9 seconds
    duration = random.randint(3, 9)
    print(f"Playing Rick Roll video for {duration} seconds...")
    
    # Path to the local MP4 file - look in script directory first, then project root
    script_dir = Path(__file__).parent
    video_file = script_dir / "RickRoll_Small.mp4"
    
    # Fallback to project root if not in script directory
    if not video_file.exists():
        video_file = Path("E:/CodeTests/P_Buttons/RickRoll_Small.mp4")
    
    if not video_file.exists():
        print(f"Video file not found: {video_file}")
        return False
    
    try:
        # Generate random window size and position in Python
        
        # Random window size (width: 400-1080, maintaining 4:3 ratio)
        window_width = random.randint(400, min(1080, 1400))
        window_height = int(window_width * 0.75)
        
        # Random position (keep window on screen)
        max_x = max(0, 1920 - window_width - 50)
        max_y = max(0, 1080 - window_height - 50)
        pos_x = random.randint(0, max_x) if max_x > 0 else 0
        pos_y = random.randint(0, max_y) if max_y > 0 else 0
        
        # Use Windows Media Player with proper timing control
        ps_script = f'''
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName PresentationFramework

$mediaElement = New-Object System.Windows.Controls.MediaElement
$mediaElement.Source = [System.Uri]::new("{video_file.as_uri()}")
$mediaElement.LoadedBehavior = [System.Windows.Controls.MediaState]::Play
$mediaElement.Volume = 1.0
$mediaElement.Stretch = [System.Windows.Media.Stretch]::Fill

$window = New-Object System.Windows.Window
$window.Content = $mediaElement
$window.Width = {window_width}
$window.Height = {window_height}
$window.Left = {pos_x}
$window.Top = {pos_y}
$window.WindowStyle = [System.Windows.WindowStyle]::None
$window.Topmost = $true
$window.Background = [System.Windows.Media.Brushes]::Black

# Timer to close window after specified duration
$timer = New-Object System.Windows.Threading.DispatcherTimer
$timer.Interval = [System.TimeSpan]::FromSeconds({duration})
$timer.Add_Tick({{
    $window.Close()
    $timer.Stop()
}})

$window.Add_Loaded({{
    $mediaElement.Play()
    $timer.Start()
}})

$window.ShowDialog() | Out-Null
'''
        
        print(f"Starting video playback in {window_width}x{window_height} window at ({pos_x},{pos_y})...")
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script
        ], capture_output=True, text=True, timeout=duration + 10)
        
        if result.returncode == 0:
            print("Rick Roll completed successfully!")
            return True
        else:
            print(f"Playback error: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"Error playing video: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("=" * 40)
    print("Prank completed!" if success else "Prank failed!")