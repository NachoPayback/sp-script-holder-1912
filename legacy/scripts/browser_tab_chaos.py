#!/usr/bin/env python3
"""
Browser Tab Explosion Prank - Opens multiple browser tabs then closes them
SMART VERSION - Uses Selenium for precise control
"""

import time


def main():
    """Main prank function using Selenium for safe browser control"""
    print("Browser Tab Chaos starting...")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("Error: Selenium not installed")
        print("Please install with: pip install selenium")
        return

    # Configure Chrome options for faster startup
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    driver = None
    try:
        # Start browser instance
        print("Starting browser...")
        driver = webdriver.Chrome(options=chrome_options)

        # URLs to open (mix of blank and harmless pages)
        urls_to_open = [
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Surprise! 🎉</h1>",
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Prank in progress... ⚡</h1>",
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Just a prank! 😄</h1>",
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Almost done... ⏰</h1>",
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Tab Chaos! 🌪️</h1>",
            "data:text/html,<h1 style='text-align:center;margin-top:200px;font-family:Arial'>Gotcha! 😆</h1>",
        ]

        # Navigate to first URL
        driver.get(urls_to_open[0])
        print("Opened first tab")

        # Open remaining URLs in new tabs
        for i, url in enumerate(urls_to_open[1:], 2):
            driver.execute_script(f"window.open('{url}', '_blank');")
            print(f"Opened tab {i}")
            time.sleep(0.3)  # Small delay for effect

        print(f"Browser chaos activated! {len(urls_to_open)} tabs opened")
        print("Tabs will stay open - close manually when you're done with the prank!")

        # Don't auto-close - let the tabs stay for maximum prank effect
        print("Browser tab chaos complete!")

    except Exception as e:
        print(f"Error during browser automation: {e}")
        try:
            # Try to clean up if something went wrong
            if driver is not None:
                driver.quit()
        except Exception:
            pass
        print("Note: If browser windows remain open, please close them manually")


if __name__ == "__main__":
    main()
