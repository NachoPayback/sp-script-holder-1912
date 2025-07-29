#!/usr/bin/env python3
"""
Fast YouTube wallpaper prank - changes desktop to random channel video thumbnail
"""

import random
import tempfile
import time

import requests

try:
    import ctypes
except ImportError:
    print("This script requires Windows")
    exit(1)


def get_channel_videos_fast(channel_handle):
    """Get videos from channel /videos page - fast method"""
    try:
        # Use the specific /videos page to avoid streams/shorts/community posts
        videos_url = f"https://www.youtube.com/@{channel_handle}/videos"
        print(f"Fetching from: {videos_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(videos_url, headers=headers, timeout=8)
        if response.status_code != 200:
            print(f"Failed to fetch videos page: {response.status_code}")
            return []

        # Extract video IDs using regex - much faster than parsing
        import re
        pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
        matches = re.findall(pattern, response.text)

        # Remove duplicates while preserving order
        seen = set()
        video_ids = []
        for match in matches:
            if match not in seen:
                video_ids.append(match)
                seen.add(match)
                if len(video_ids) >= 30:  # Limit for speed
                    break

        print(f"Found {len(video_ids)} videos")
        return video_ids

    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []


def set_wallpaper_fast(image_url):
    """Download and set wallpaper in one go - fastest method"""
    try:
        # Download image directly to temp file
        response = requests.get(image_url, timeout=5, stream=True)
        if response.status_code != 200:
            return None, None

        # Create temp file and write image data
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        temp_file.close()

        # Set wallpaper immediately
        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02

        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            temp_file.name,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )

        if result:
            return temp_file.name, True
        else:
            return temp_file.name, False

    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        return None, False


def get_current_wallpaper():
    """Get current wallpaper path"""
    try:
        SPI_GETDESKWALLPAPER = 0x0073
        buffer = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETDESKWALLPAPER, 512, buffer, 0
        )
        return buffer.value
    except Exception:
        return None


def restore_wallpaper(wallpaper_path):
    """Restore original wallpaper"""
    try:
        if wallpaper_path:
            SPI_SETDESKWALLPAPER = 0x0014
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDCHANGE = 0x02

            ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                wallpaper_path,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
            )
            return True
    except Exception:
        pass
    return False


def main():
    """Fast wallpaper prank"""
    print("Fast YouTube Wallpaper Prank starting...")

    # Get current wallpaper
    original_wallpaper = get_current_wallpaper()
    print(f"Current wallpaper: {original_wallpaper}")

    # Get videos from ScammerPayback /videos page only
    video_ids = get_channel_videos_fast("ScammerPayback")

    if not video_ids:
        print("No videos found")
        return

    # Pick random video and build thumbnail URL
    random_video = random.choice(video_ids)
    thumbnail_url = f"https://img.youtube.com/vi/{random_video}/maxresdefault.jpg"

    print(f"Selected: https://youtube.com/watch?v={random_video}")
    print("Setting wallpaper...")

    # Download and set wallpaper in one operation
    temp_file, success = set_wallpaper_fast(thumbnail_url)

    if success:
        print("Wallpaper changed! Restoring in 5 seconds...")
        time.sleep(5)

        # Restore original
        if restore_wallpaper(original_wallpaper):
            print("Original wallpaper restored")
        else:
            print("Could not restore original wallpaper")
    else:
        print("Failed to change wallpaper")

    # Clean up
    if temp_file:
        try:
            import os
            os.unlink(temp_file)
        except Exception:
            pass

    print("Done!")


if __name__ == "__main__":
    main()
