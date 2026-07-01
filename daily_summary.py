"""Daily summary — run by the PythonAnywhere scheduled task.

Schedule it at 18:30 UTC, which is 00:00 IST. It summarizes the day that just
ended (yesterday, IST) and sends it to the owner.

    python daily_summary.py
"""

from datetime import datetime, timedelta

import config
import db
from summary import build_daily_summary
from telegram_api import send_message


def main():
    if not config.OWNER_ID:
        print("OWNER_ID not set — nothing to send.")
        return

    db.init_db()
    day = (datetime.now(config.TIMEZONE) - timedelta(days=1)).date()
    expenses = db.get_expenses_for_day(config.OWNER_ID, day)
    text = build_daily_summary(expenses, day.strftime("%d %b %Y"))
    resp = send_message(config.OWNER_ID, text, parse_mode="Markdown")
    print(f"Daily summary for {day} sent — HTTP {resp.status_code}")


if __name__ == "__main__":
    main()
