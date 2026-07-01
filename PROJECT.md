# Tele Expense Manager

A personal expense tracker that lives entirely inside a **Telegram chat**. You log
expenses by simply texting them as they happen, and at the end of each day the bot
sends back a summary of everything you spent.

No app to open, no spreadsheet to maintain — just chat.

---

## What it is

Tele Expense Manager is a Telegram bot backed by a small service and a database.
It parses your chat messages into structured expense records (item, amount,
category), stores them, and delivers a daily rollup at midnight.

The design goal for **v1** is deliberately minimal: capture expenses with zero
friction and get one useful summary per day.

---

## Core Flow (v1)

1. **Log as you go** — You send an expense to the bot as it happens, e.g.
   `Coffee 120 food` or `Uber 250 travel`.
2. **Auto-register** — The bot parses the message, records the item, amount, and
   category, confirms it, and keeps a running tally for the day.
3. **Daily summary** — At **00:00 IST** (Asia/Kolkata, UTC+5:30) the bot sends a
   summary of the day's spending: a per-item breakdown and totals, optionally
   rendered as a chart.

---

## The Summary / Chart

Each daily summary is built from the day's records and shows, per expense:

| Field      | Description                                  | Example   |
|------------|----------------------------------------------|-----------|
| Item       | What the money was spent on                  | Coffee    |
| Amount     | Money spent on that item                     | 120       |
| Category   | The category **you** assigned                | Food      |

Plus:

- **Total spent** for the day
- **Per-category totals** (e.g. Food: ₹340, Travel: ₹250)

The v1 summary is a **table** (text/Markdown), not an image. A visual chart
(pie/bar image) is a later addition.

All amounts are in **Indian Rupees (₹)** — v1 is single-currency.

Categories are **user-defined** — you decide them when logging (no fixed taxonomy
in v1).

---

## Message Format & Parsing

Logging must be fast and forgiving — **no fixed word order and no punctuation
required**. The bot figures out the three pieces from whatever you type:

```
coffee 120 food
120 coffee food
food 120 coffee
```

...should all register the same expense.

**How the parser identifies each piece:**

- **Amount** — the numeric token (with or without `₹`, e.g. `120` or `₹120`).
  Easy to pick out since it's the only number.
- **Category** — the token that matches one of your **registered categories**.
  Position doesn't matter.
- **Item** — whatever text is left over after amount and category are removed.
  This is naturally **multi-word**: since the amount and category are pinned, any
  remaining words form the item (e.g. `metro card 500 travel` → item = "metro card").

**Behaviour on a successful log:** the bot stays **silent** (no per-expense
confirmation) — it just records it.

**When no token matches a registered category:** the bot **replies asking you to
register/assign a category** for that expense (it does not guess). This is what
keeps free word order unambiguous — the only way to know which word is the
category is to match it against the known list.

### Categories are registered first

Categories are managed with a small command, e.g.:

```
/addcategory food travel entertainment
/categories        → list current categories
/delcategory food  → remove one
```

Once registered, a category is recognised in **any position**, so all of these log
the same expense:

```
coffee 120 food
120 food coffee
food coffee 120
```

If a message uses a word that isn't a registered category, the bot asks you to add
it (via `/addcategory`) — after which that word is known forever.

**Starter set:** on first use, the bot seeds a default set of categories so logging
works immediately:

```
food · travel · groceries · bills · entertainment · shopping · health
```

You can edit this list anytime with `/addcategory` / `/delcategory`.

---

## High-Level Architecture

```
You ──(text)──▶ Telegram ──▶ Bot (webhook/polling)
                                │
                                ├─ parse message → {item, amount, category}
                                ├─ store in DB (silent on success)
                                └─ reply ONLY if category is unknown → ask for it
                                │
        Scheduler (00:00 IST) ──┴─▶ build daily summary table ──▶ send to you
```

**Components**

- **Bot handler** — receives Telegram messages, parses them, saves expenses
  silently; replies only to ask for an unknown category or to handle category
  commands.
- **Storage** — a database of expense records and registered categories.
- **Scheduler** — a cron/timer job that fires at 00:00 IST (Asia/Kolkata),
  aggregates the day's records, builds the summary table, and sends it.

---

## Data Model (draft)

**expenses**

| Column      | Type      | Notes                              |
|-------------|-----------|------------------------------------|
| id          | integer   | primary key                        |
| user_id     | integer   | Telegram user/chat id              |
| item        | text      | what was bought (can be multi-word)|
| amount      | numeric   | money spent (₹)                    |
| category    | text      | matched registered category        |
| created_at  | timestamp | stored in UTC; rolled up per IST day|

**categories**

| Column      | Type      | Notes                              |
|-------------|-----------|------------------------------------|
| id          | integer   | primary key                        |
| user_id     | integer   | Telegram user/chat id              |
| name        | text      | registered category (unique/user)  |

> Seeded on first use with the starter set: food, travel, groceries, bills,
> entertainment, shopping, health.

---

## Tech Stack (decided)

- **Language:** Python
- **Bot framework:** `python-telegram-bot` (has a built-in job queue for the
  midnight schedule)
- **Storage:** SQLite (zero-setup, perfect for a single user)
- **Scheduling:** the framework's job queue (fires at 00:00 IST)
- **Charts:** `matplotlib` — *later only*, not in v1
- **Deploy:** **PythonAnywhere (free tier)** — always-on, no card required. Runs the
  **webhook** version (`flask_app.py`) as a WSGI web app. The core modules (`db`,
  `expense_parser`, `summary`, `config`) are shared with the local polling bot
  (`bot.py`) unchanged. SQLite file persists on PythonAnywhere.
- **Daily summary trigger:** PythonAnywhere's free tier has **no scheduled tasks**, so
  a free external scheduler (cron-job.org, or GitHub Actions) hits a protected endpoint
  `GET /tasks/daily/<WEBHOOK_SECRET>` once a day at 00:00 IST, which sends the summary.
  - *Alternative:* an always-on Linux VM (Oracle/GCP free tier) running `bot.py` via
    systemd — rejected for v1 because both require a card at signup.

### How you use it (access model)

You interact with the bot entirely through the **Telegram app on your phone**.
Telegram is the middleman: your phone ↔ Telegram ↔ bot process (on PythonAnywhere).
Your phone never connects to the server directly, so the server just needs to be
online 24/7 — which the PythonAnywhere web app provides.

### Two transports, same brain

- **Local / polling** (`bot.py`) — long-polling via python-telegram-bot; good for
  testing on your laptop.
- **Cloud / webhook** (`flask_app.py` + `daily_summary.py`) — Telegram pushes updates
  to a Flask app; the midnight summary is a scheduled task. This is the deployed path.

Both share the parsing, storage, and summary logic, so behaviour is identical.

---

## Scope

**In scope for v1**
- Log expenses via chat message
- Parse item / amount / category with **free word order** and no required punctuation
- Store records
- Daily summary **table** at 00:00 IST
- User-defined categories, **registered via commands** (`/addcategory`,
  `/categories`, `/delcategory`) and recognised in any position
- Silent on successful log; only replies when a category is unknown
- **Single-owner lock** — bot responds only to your Telegram user ID
- **Decimal amounts** allowed (₹120.50) as well as whole rupees
- **Unparseable messages** (no amount) get a short "couldn't read that" reply
- **Empty-day summary** — bot still messages "no expenses today" at midnight

**Out of scope for v1 (ideas for later)**
- Editing / deleting a logged expense
- Weekly / monthly / custom-range reports
- Budgets and overspend alerts
- Multi-currency handling
- Multiple users / shared ledgers
- Natural-language parsing (e.g. "spent 200 on lunch")
- Export to CSV / Google Sheets

---

## Behaviour Rules (decided)

- **Access:** bot only responds to the owner's Telegram user ID; everyone else is
  ignored / told they're not authorized.
- **Amounts:** decimals allowed (`₹120.50`) as well as whole rupees; `₹` optional.
- **Successful log:** silent — no confirmation message.
- **Unknown category:** reply asking to register it via `/addcategory`.
- **Unparseable message (no amount found):** short reply — *"couldn't read that as
  an expense"* — so nothing is silently dropped.
- **Empty day:** at 00:00 IST, still send a summary — *"No expenses logged today —
  ₹0 spent."*

---

## Open Questions

*All resolved — see Behaviour Rules above. History kept for reference:*

- ~~**Timezone**~~ → Asia/Kolkata (IST, UTC+5:30).
- ~~**Confirmation style**~~ → silent on success; reply only when a category is unknown.
- ~~**Chart vs. text**~~ → v1 summary is a text/Markdown table; visual chart is later.
- ~~**Category fallback**~~ → ask the user to register a category (no silent fallback).
- ~~**Item vs. category disambiguation**~~ → categories registered first (`/addcategory`);
  matched against the registered list in any position.
- ~~**Access control**~~ → single-owner lock by Telegram user ID.
- ~~**Amount precision**~~ → decimals allowed.
- ~~**Bad input**~~ → reply that it couldn't be read.
- ~~**Empty day**~~ → send "no expenses today".

---

## Getting Started (planned)

1. Create a bot with [@BotFather](https://t.me/BotFather) and get the token.
2. Set the token as an environment variable (e.g. `TELEGRAM_BOT_TOKEN`).
3. Run the service; start chatting your expenses.
4. Receive your first daily summary at midnight.

---

*Status: v1 spec complete — all design questions resolved; ready to build.*
