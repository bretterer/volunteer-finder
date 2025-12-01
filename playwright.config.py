"""
Playwright configuration for end-to-end testing.
"""

# Browser configuration
BROWSER = "chromium"
HEADLESS = True
SLOW_MO = 0  # Milliseconds between actions (useful for debugging)

# Timeout settings (in milliseconds)
DEFAULT_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 30000

# Screenshot settings
SCREENSHOT_ON_FAILURE = True

# Video recording settings
VIDEO_ON = False
