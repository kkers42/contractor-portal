"""
Centralized logging utility with Discord webhook integration
Sends ERROR and CRITICAL logs to Discord for monitoring
"""

import logging
import requests
import traceback
import os
from datetime import datetime
from pathlib import Path

# Read version from VERSION file
VERSION_FILE = Path(__file__).parent.parent.parent / "VERSION"
try:
    with open(VERSION_FILE, 'r') as f:
        APP_VERSION = f.read().strip()
except:
    APP_VERSION = "unknown"

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1454668498012864604/IbXxlME8951eXE8GEMJgHDC7A_t_t4ZYI9_5t3f5b7hJ6HJaXtO5g7bJhG1GpUW6Ocbi"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def send_to_discord(level: str, logger_name: str, message: str, exc_info=None):
    """Send log message to Discord webhook"""
    try:
        # Color coding: ERROR=red, CRITICAL=dark red, WARNING=yellow
        color_map = {
            "ERROR": 0xFF0000,      # Red
            "CRITICAL": 0x8B0000,   # Dark Red
            "WARNING": 0xFFFF00     # Yellow
        }

        embed = {
            "title": f"🚨 {level}: {logger_name}",
            "description": message[:4000],  # Discord limit
            "color": color_map.get(level, 0x808080),
            "fields": [
                {
                    "name": "Version",
                    "value": f"v{APP_VERSION}",
                    "inline": True
                },
                {
                    "name": "Timestamp",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": True
                }
            ]
        }

        # Add traceback if exception info provided
        if exc_info:
            tb = ''.join(traceback.format_exception(*exc_info))
            embed["fields"].append({
                "name": "Traceback",
                "value": f"```python\n{tb[:1000]}\n```",  # Limit traceback length
                "inline": False
            })

        payload = {
            "embeds": [embed],
            "username": "Contractor App Monitor"
        }

        # Send to Discord (timeout 5 seconds, don't block app)
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)

    except Exception as e:
        # Don't let Discord failures break the app
        print(f"[WARNING] Failed to send log to Discord: {str(e)}")

class DiscordHandler(logging.Handler):
    """Custom logging handler that sends ERROR+ logs to Discord"""

    def emit(self, record):
        try:
            if record.levelno >= logging.ERROR:
                send_to_discord(
                    level=record.levelname,
                    logger_name=record.name,
                    message=record.getMessage(),
                    exc_info=record.exc_info
                )
        except Exception:
            self.handleError(record)

# Create Discord handler
discord_handler = DiscordHandler()
discord_handler.setLevel(logging.ERROR)

# Add Discord handler to root logger
logging.getLogger().addHandler(discord_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with Discord integration"""
    return logging.getLogger(name)

# Example usage:
# from app.utils.logger import get_logger
# logger = get_logger(__name__)
# logger.error("Something went wrong", exc_info=True)
