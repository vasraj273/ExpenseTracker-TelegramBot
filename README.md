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

## Deploy: always-on, free (Oracle Cloud Always Free)

Your laptop isn't always on, so run the bot on a free 24/7 VM. Telegram is the
middleman — you keep chatting from your phone; the VM just needs to stay online.

1. **Create the VM** — Sign up at Oracle Cloud (Always Free). Create a Compute
   instance with an **Ubuntu** image (the Always Free ARM/AMD shapes are fine).
   Save the SSH key.
2. **SSH in and set up:**
   ```bash
   sudo apt update && sudo apt install -y python3-venv git
   git clone <your-repo-url> tele-expense-manager
   cd tele-expense-manager
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env && nano .env     # paste token + OWNER_ID
   ```
3. **Run it as a service** so it restarts on reboot/crash. Create
   `/etc/systemd/system/expense-bot.service`:
   ```ini
   [Unit]
   Description=Tele Expense Manager
   After=network-online.target

   [Service]
   WorkingDirectory=/home/ubuntu/tele-expense-manager
   ExecStart=/home/ubuntu/tele-expense-manager/.venv/bin/python bot.py
   Restart=always
   User=ubuntu

   [Install]
   WantedBy=multi-user.target
   ```
   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now expense-bot
   sudo systemctl status expense-bot     # check it's running
   journalctl -u expense-bot -f          # live logs
   ```

The bot uses **long polling** (no public IP/webhook/port needed), so no firewall
changes are required. The SQLite file (`expenses.db`) lives next to the code and
persists on the VM disk.

---

## Notes & limits (v1)

- Single user (you), single currency (₹).
- No edit/delete of a logged expense yet, and no weekly/monthly reports — see the
  "out of scope" list in [PROJECT.md](PROJECT.md) for the roadmap.
