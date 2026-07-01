# Tele Expense Manager

A personal expense tracker that runs entirely inside a **Telegram chat**. Text your
expenses as they happen; get a daily summary table at **00:00 IST**.

> Full design/spec: [PROJECT.md](PROJECT.md)

---

## How it works

- Text an expense in any word order: `coffee 120 food` = `120 food coffee` = `food coffee 120`
- The **number** is the amount (₹, decimals, commas ok), a **registered category**
  word is the category, everything else is the item.
- Successful logs are **silent**. The bot only replies to ask for an unknown
  category or when it can't read a message.
- At **00:00 IST** it sends a summary table of the day that just ended.

Categories are registered first (a starter set is seeded on first use):

```
/addcategory fuel snacks     add categories
/categories                  list them
/delcategory snacks          remove one
```

Other commands: `/start`, `/summary` (today so far), `/myid`.

---

## Files

| File                 | Purpose                                             |
|----------------------|-----------------------------------------------------|
| `bot.py`             | Telegram handlers, access lock, daily job, entry    |
| `expense_parser.py`  | Turns a message into {item, amount, category}        |
| `db.py`              | SQLite storage (expenses + categories)              |
| `summary.py`         | Builds the daily summary table                      |
| `config.py`          | Env/config (token, owner id, timezone, starter set) |

**Deployment (PythonAnywhere webhook) — reuses the core modules above:**

| File                      | Purpose                                              |
|---------------------------|------------------------------------------------------|
| `flask_app.py`            | Webhook web app (Flask) — same behaviour as bot.py   |
| `daily_summary.py`        | Scheduled task that sends the midnight summary        |
| `set_webhook.py`          | One-time: registers the Telegram webhook             |
| `telegram_api.py`         | Tiny Telegram API sender (via requests)              |
| `wsgi_pythonanywhere.py`  | Sample WSGI config to paste into PythonAnywhere      |
| `requirements-webhook.txt`| Deps for the webhook deployment (Flask, requests)    |

Two ways to run: **local polling** (`bot.py`, good for testing) or
**PythonAnywhere webhook** (always-on, free, no card — see below).

---

## Run it locally (to test)

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # then edit .env
python bot.py
```

### Getting the two values in `.env`

1. **`TELEGRAM_BOT_TOKEN`** — In Telegram, message **@BotFather** → `/newbot` →
   choose a name & username → it gives you a token. Paste it in.
2. **`OWNER_ID`** — Leave it blank for now and start the bot. In Telegram, open your
   new bot and send `/myid`; it replies with your numeric id. Put that in `.env` as
   `OWNER_ID` and restart. (This locks the bot to only you.)

Then send `/start`, add categories, and start logging.

---

## Deploy: always-on, free, no card (PythonAnywhere)

PythonAnywhere runs the bot 24/7 in the cloud for free, with **no card required**.
It uses the **webhook** version (`flask_app.py`) plus a **daily scheduled task**
(`daily_summary.py`). You keep chatting from your phone; PythonAnywhere stays online.

> Domain assumed below: `shypurr.pythonanywhere.com` (username `ShyPurr`). Adjust to
> your own. Home path shown as `/home/ShyPurr/...` — confirm yours with `pwd`.

### 1. Get the code onto PythonAnywhere (Bash console)
```bash
git clone https://github.com/vasraj273/ExpenseTracker-TelegramBot.git
cd ExpenseTracker-TelegramBot
pip install --user -r requirements-webhook.txt   # Flask/requests usually preinstalled
```

### 2. Create `.env`
```bash
cp .env.example .env
nano .env
```
Fill in `TELEGRAM_BOT_TOKEN`, `OWNER_ID`, and a `WEBHOOK_SECRET`. Generate a secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3. Create the web app
- **Web** tab → **Add a new web app** → **Manual configuration** → your Python version.
- Open the **WSGI configuration file** link and replace its contents with what's in
  `wsgi_pythonanywhere.py` (set `PROJECT_PATH` to the folder from `pwd`).
- Click the big green **Reload** button.
- Visit `https://shypurr.pythonanywhere.com/` — it should say
  *"Tele Expense Manager is running."*

### 4. Register the webhook (Bash console)
```bash
python set_webhook.py https://shypurr.pythonanywhere.com
```
This points Telegram at `/webhook/<secret>`. Now message your bot `/start`.

### 5. Schedule the daily summary
- **Tasks** tab → add a **Scheduled task**:
  ```
  python /home/ShyPurr/ExpenseTracker-TelegramBot/daily_summary.py
  ```
- Set the time to **18:30 UTC** — that's **00:00 IST**.

### Keeping it alive (free-tier quirks)
- Every ~3 months PythonAnywhere emails you to click **"Run until 3 months from now"**
  on the Web tab. Miss it and the bot pauses (data is safe) until you click.
- The `expenses.db` SQLite file lives next to the code and persists.
- After any `git pull` of new code, hit **Reload** on the Web tab.

*(An always-on Linux VM — Oracle Cloud / Google Cloud free tier — is an alternative
if you ever want one; those use `bot.py` via a `systemd` service, but they require a
card for signup.)*

---

## Notes & limits (v1)

- Single user (you), single currency (₹).
- No edit/delete of a logged expense yet, and no weekly/monthly reports — see the
  "out of scope" list in [PROJECT.md](PROJECT.md) for the roadmap.
