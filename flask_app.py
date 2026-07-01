"""Webhook version of the bot for PythonAnywhere (WSGI / Flask).

Telegram pushes each update to /webhook/<secret>. Same behaviour as bot.py, but
synchronous and driven by webhooks instead of long-polling. Core logic
(parsing, storage, summary) is reused unchanged.
"""

from datetime import datetime

from flask import Flask, request

import config
import db
from expense_parser import parse_message
from summary import build_daily_summary
from telegram_api import send_message

db.init_db()

app = Flask(__name__)


@app.get("/")
def index():
    return "Tele Expense Manager is running.", 200


@app.post("/webhook/<secret>")
def webhook(secret):
    # Path secret + Telegram's secret_token header (defense in depth).
    if not config.WEBHOOK_SECRET or secret != config.WEBHOOK_SECRET:
        return "forbidden", 403
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != config.WEBHOOK_SECRET:
        return "forbidden", 403

    update = request.get_json(force=True, silent=True) or {}
    message = update.get("message") or update.get("edited_message")
    if message and message.get("text"):
        _handle(message)
    return "ok", 200


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #

def _handle(message):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id")
    text = message["text"].strip()
    if not text:
        return

    first = text.split()[0].split("@")[0].lower()

    # /myid works for anyone (needed to configure OWNER_ID).
    if first == "/myid":
        send_message(chat_id, f"Your Telegram ID: {user_id}")
        return

    # Access control / first-run setup.
    if config.OWNER_ID == 0:
        send_message(
            chat_id,
            "⚙️ Setup needed: OWNER_ID isn't set yet.\n"
            f"Your Telegram ID is: {user_id}\n"
            "Put it in .env, then reload the web app.",
        )
        return
    if user_id != config.OWNER_ID:
        send_message(chat_id, "⛔ Not authorized.")
        return

    if text.startswith("/"):
        _handle_command(chat_id, user_id, text)
    else:
        _handle_expense(chat_id, user_id, text)


def _handle_command(chat_id, user_id, text):
    parts = text.split()
    cmd = parts[0].lstrip("/").split("@")[0].lower()
    args = parts[1:]

    if cmd in ("start", "help"):
        seeded = db.seed_starter_categories(user_id)
        cats = ", ".join(db.get_categories(user_id))
        intro = "🌱 Seeded starter categories.\n\n" if seeded else ""
        send_message(
            chat_id,
            intro
            + "👋 Expense tracker ready.\n\n"
            "Text an expense as it happens, e.g.\n  coffee 120 food\n"
            "Word order doesn't matter — '120 food coffee' works too.\n"
            "I stay silent when a log succeeds.\n\n"
            f"Your categories: {cats}\n\n"
            "Commands:\n"
            "/categories — list categories\n"
            "/addcategory <names> — add categories\n"
            "/delcategory <name> — remove a category\n"
            "/summary — today's expenses so far\n"
            "/myid — show your Telegram ID",
        )
    elif cmd == "categories":
        db.seed_starter_categories(user_id)
        send_message(chat_id, "Categories: " + ", ".join(db.get_categories(user_id)))
    elif cmd == "addcategory":
        if not args:
            send_message(chat_id, "Usage: /addcategory food travel")
            return
        added = db.add_categories(user_id, args)
        send_message(
            chat_id,
            "✅ Added: " + ", ".join(added) if added else "Nothing new to add — those already exist.",
        )
    elif cmd == "delcategory":
        if not args:
            send_message(chat_id, "Usage: /delcategory food")
            return
        ok = db.delete_category(user_id, args[0])
        send_message(
            chat_id,
            f"🗑 Removed '{args[0].lower()}'." if ok else f"'{args[0]}' isn't a category.",
        )
    elif cmd == "summary":
        today = datetime.now(config.TIMEZONE).date()
        exp = db.get_expenses_for_day(user_id, today)
        label = today.strftime("%d %b %Y") + " (so far)"
        send_message(chat_id, build_daily_summary(exp, label), parse_mode="Markdown")
    else:
        send_message(chat_id, "Unknown command. Try /help.")


def _handle_expense(chat_id, user_id, text):
    db.seed_starter_categories(user_id)
    known = db.get_categories(user_id)
    result = parse_message(text, known)

    if result.status == "no_amount":
        send_message(
            chat_id,
            "⚠️ Couldn't read that as an expense (no amount found).\nTry: coffee 120 food",
        )
        return
    if result.status == "unknown_category":
        leftover = " ".join(result.unknown_tokens)
        send_message(
            chat_id,
            f"🤔 Found the amount but no known category in “{leftover}”.\n"
            "Register it first: /addcategory <name>, then resend the expense.",
        )
        return

    # success — log silently, no reply
    db.add_expense(user_id, result.item, result.amount, result.category)
