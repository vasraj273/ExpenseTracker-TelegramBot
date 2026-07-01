"""Configuration loaded from environment (.env).

Works for both the local polling bot (bot.py) and the PythonAnywhere webhook
deployment (flask_app.py / daily_summary.py).
"""

import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent

# Load .env from this file's directory (so scheduled tasks work regardless of cwd).
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # python-dotenv not installed (e.g. env vars set another way) — that's fine.
    pass

# --- Telegram ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Your numeric Telegram user id. The bot only responds to this user.
# Message the bot /myid to find yours, then set it here (in .env).
OWNER_ID = int(os.getenv("OWNER_ID", "0") or "0")

# Secret used in the webhook URL path + Telegram secret_token header.
# Only needed for the PythonAnywhere (webhook) deployment. Make it a long random
# string, e.g.  python -c "import secrets; print(secrets.token_urlsafe(24))"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

# --- Storage ---
# Absolute path so the web app and the scheduled task share the same file.
DB_PATH = os.getenv("DB_PATH") or str(BASE_DIR / "expenses.db")

# --- Time ---
# User is in Ahmedabad, India. Everything time-related uses IST.
TIMEZONE = ZoneInfo("Asia/Kolkata")

# Daily summary fires at this local (IST) time (used by the polling bot's job queue).
SUMMARY_HOUR = 0
SUMMARY_MINUTE = 0

# --- Categories ---
# Seeded on first use so logging works immediately.
STARTER_CATEGORIES = [
    "food",
    "travel",
    "groceries",
    "bills",
    "entertainment",
    "shopping",
    "health",
]
