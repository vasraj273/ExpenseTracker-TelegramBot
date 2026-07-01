"""Minimal Telegram Bot API calls via `requests`.

Used by the webhook app and the scheduled summary task (both sync). Keeps the
PythonAnywhere deployment free of the async python-telegram-bot dependency.
"""

import requests

from config import BOT_TOKEN

_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    return requests.post(f"{_API}/sendMessage", data=data, timeout=30)
