"""Tele Expense Manager — a personal expense tracker that runs on Telegram.

Log expenses by texting them (any word order); get a daily summary at 00:00 IST.
See PROJECT.md for the full spec.
"""

import logging
from datetime import datetime, time, timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import db
from expense_parser import parse_message
from summary import build_daily_summary

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tele-expense-manager")


# --------------------------------------------------------------------------- #
# Access control (single-owner lock)
# --------------------------------------------------------------------------- #

async def _authorized(update: Update) -> bool:
    """True if the sender may use the bot. Handles the unconfigured case too."""
    user = update.effective_user
    uid = user.id if user else None

    if config.OWNER_ID == 0:
        # Not linked to an owner yet — help the user configure themselves.
        await update.message.reply_text(
            "⚙️ Setup needed: this bot isn't linked to an owner yet.\n"
            f"Your Telegram ID is: {uid}\n"
            "Put it in your .env as OWNER_ID, then restart the bot."
        )
        return False

    if uid != config.OWNER_ID:
        await update.message.reply_text("⛔ Not authorized.")
        return False

    return True


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id if update.effective_user else "unknown"
    await update.message.reply_text(f"Your Telegram ID: {uid}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    uid = update.effective_user.id
    seeded = db.seed_starter_categories(uid)
    cats = ", ".join(db.get_categories(uid))
    intro = ""
    if seeded:
        intro = "🌱 Seeded starter categories.\n\n"
    await update.message.reply_text(
        intro
        + "👋 Expense tracker ready.\n\n"
        "Just text an expense as it happens, e.g.\n"
        "  coffee 120 food\n"
        "Word order doesn't matter — '120 food coffee' works too.\n"
        "I stay silent when a log succeeds.\n\n"
        f"Your categories: {cats}\n\n"
        "Commands:\n"
        "/categories — list categories\n"
        "/addcategory <names> — add categories\n"
        "/delcategory <name> — remove a category\n"
        "/summary — today's expenses so far\n"
        "/myid — show your Telegram ID"
    )


async def cmd_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    uid = update.effective_user.id
    db.seed_starter_categories(uid)
    await update.message.reply_text("Categories: " + ", ".join(db.get_categories(uid)))


async def cmd_addcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /addcategory food travel")
        return
    added = db.add_categories(update.effective_user.id, context.args)
    if added:
        await update.message.reply_text("✅ Added: " + ", ".join(added))
    else:
        await update.message.reply_text("Nothing new to add — those already exist.")


async def cmd_delcategory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /delcategory food")
        return
    name = context.args[0]
    ok = db.delete_category(update.effective_user.id, name)
    await update.message.reply_text(
        f"🗑 Removed '{name.lower()}'." if ok else f"'{name}' isn't a category."
    )


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    uid = update.effective_user.id
    today = datetime.now(config.TIMEZONE).date()
    expenses = db.get_expenses_for_day(uid, today)
    label = today.strftime("%d %b %Y") + " (so far)"
    await update.message.reply_text(
        build_daily_summary(expenses, label), parse_mode=ParseMode.MARKDOWN
    )


# --------------------------------------------------------------------------- #
# Expense messages
# --------------------------------------------------------------------------- #

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _authorized(update):
        return
    uid = update.effective_user.id
    db.seed_starter_categories(uid)
    known = db.get_categories(uid)
    result = parse_message(update.message.text, known)

    if result.status == "no_amount":
        await update.message.reply_text(
            "⚠️ Couldn't read that as an expense (no amount found).\n"
            "Try: coffee 120 food"
        )
        return

    if result.status == "unknown_category":
        leftover = " ".join(result.unknown_tokens)
        await update.message.reply_text(
            f"🤔 Found the amount but no known category in “{leftover}”.\n"
            "Register it first: /addcategory <name>, then resend the expense."
        )
        return

    # success — log silently, no reply
    db.add_expense(uid, result.item, result.amount, result.category)


# --------------------------------------------------------------------------- #
# Scheduled daily summary
# --------------------------------------------------------------------------- #

async def send_daily_summary(context: ContextTypes.DEFAULT_TYPE):
    """Fires at 00:00 IST — summarizes the day that just ended (yesterday IST)."""
    uid = config.OWNER_ID
    if not uid:
        logger.warning("OWNER_ID not set; skipping daily summary.")
        return
    day = (datetime.now(config.TIMEZONE) - timedelta(days=1)).date()
    expenses = db.get_expenses_for_day(uid, day)
    await context.bot.send_message(
        chat_id=uid,
        text=build_daily_summary(expenses, day.strftime("%d %b %Y")),
        parse_mode=ParseMode.MARKDOWN,
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main():
    if not config.BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set — see .env.example")

    db.init_db()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("addcategory", cmd_addcategory))
    app.add_handler(CommandHandler("delcategory", cmd_delcategory))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    app.job_queue.run_daily(
        send_daily_summary,
        time=time(
            hour=config.SUMMARY_HOUR,
            minute=config.SUMMARY_MINUTE,
            tzinfo=config.TIMEZONE,
        ),
    )

    logger.info("Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
