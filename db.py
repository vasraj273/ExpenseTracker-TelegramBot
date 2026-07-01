"""SQLite storage for expenses and user-registered categories.

Timestamps are stored as UTC epoch seconds. Day roll-ups are computed against
IST day boundaries (see config.TIMEZONE).
"""

import sqlite3
from datetime import datetime, timedelta, timezone

from config import DB_PATH, STARTER_CATEGORIES, TIMEZONE


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name    TEXT    NOT NULL,
                UNIQUE(user_id, name)
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                item       TEXT    NOT NULL,
                amount     REAL    NOT NULL,
                category   TEXT    NOT NULL,
                created_at INTEGER NOT NULL   -- UTC epoch seconds
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user_time
                ON expenses(user_id, created_at);
            """
        )


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #

def get_categories(user_id):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name FROM categories WHERE user_id = ? ORDER BY name",
            (user_id,),
        ).fetchall()
    return [r["name"] for r in rows]


def add_categories(user_id, names):
    """Add categories (stored lowercased). Returns the list actually added."""
    existing = set(get_categories(user_id))
    added = []
    with _connect() as conn:
        for raw in names:
            name = raw.strip().lower()
            if not name or name in existing:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO categories(user_id, name) VALUES (?, ?)",
                (user_id, name),
            )
            existing.add(name)
            added.append(name)
    return added


def delete_category(user_id, name):
    """Remove a category. Returns True if something was deleted."""
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM categories WHERE user_id = ? AND name = ?",
            (user_id, name.strip().lower()),
        )
    return cur.rowcount > 0


def seed_starter_categories(user_id):
    """Seed the starter set only if the user has none yet. Returns True if seeded."""
    if get_categories(user_id):
        return False
    add_categories(user_id, STARTER_CATEGORIES)
    return True


# --------------------------------------------------------------------------- #
# Expenses
# --------------------------------------------------------------------------- #

def add_expense(user_id, item, amount, category):
    ts = int(datetime.now(timezone.utc).timestamp())
    with _connect() as conn:
        conn.execute(
            "INSERT INTO expenses(user_id, item, amount, category, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, item, amount, category, ts),
        )


def _ist_day_bounds(day):
    """Return (start_epoch, end_epoch) in UTC seconds for the given IST date."""
    start = datetime(day.year, day.month, day.day, tzinfo=TIMEZONE)
    end = start + timedelta(days=1)
    return int(start.timestamp()), int(end.timestamp())


def get_expenses_for_day(user_id, day):
    """All expenses whose IST timestamp falls on `day` (a date), oldest first."""
    start, end = _ist_day_bounds(day)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT item, amount, category, created_at FROM expenses "
            "WHERE user_id = ? AND created_at >= ? AND created_at < ? "
            "ORDER BY created_at",
            (user_id, start, end),
        ).fetchall()
    return [dict(r) for r in rows]
