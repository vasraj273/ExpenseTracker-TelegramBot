"""Daily summary of the day that just ended (yesterday, IST).

Two ways this runs:
  * Manually / console:      python daily_summary.py
  * Triggered over HTTP:     the /tasks/daily/<secret> endpoint in flask_app.py
                             (hit once a day at 00:00 IST by an external scheduler)
"""

from datetime import datetime, timedelta

import config
import db
from summary import build_daily_summary
from telegram_api import send_message


def run():
    """Build and send yesterday's summary. Returns a short status string."""
    if not config.OWNER_ID:
        return "OWNER_ID not set — nothing to send."

    db.init_db()
    day = (datetime.now(config.TIMEZONE) - timedelta(days=1)).date()
    expenses = db.get_expenses_for_day(config.OWNER_ID, day)
    text = build_daily_summary(expenses, day.strftime("%d %b %Y"))
    resp = send_message(config.OWNER_ID, text, parse_mode="Markdown")
    return f"Daily summary for {day} sent — HTTP {resp.status_code}"


def main():
    print(run())


if __name__ == "__main__":
    main()
