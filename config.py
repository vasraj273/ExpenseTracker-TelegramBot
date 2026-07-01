"""Configuration loaded from environment (.env)."""

import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

# --- Telegram ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Your numeric Telegram user id. The bot only responds to this user.
# Message the bot /myid to find yours, then set it here (in .env).
OWNER_ID = int(os.getenv("OWNER_ID", "0") or "0")

# --- Storage ---
DB_PATH = os.getenv("DB_PATH", "expenses.db")

# --- Time ---
# User is in Ahmedabad, India. Everything time-related uses IST.
TIMEZONE = ZoneInfo("Asia/Kolkata")

# Daily summary fires at this local (IST) time.
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
