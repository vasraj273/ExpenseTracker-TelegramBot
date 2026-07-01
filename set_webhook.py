"""One-time helper to register (or delete) the Telegram webhook.

Run from a PythonAnywhere Bash console after the web app is live:

    python set_webhook.py https://shypurr.pythonanywhere.com

It appends /webhook/<WEBHOOK_SECRET> automatically and registers the secret
token. Use `python set_webhook.py --delete` to remove the webhook.
"""

import sys

import requests

import config

_API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"


def _check():
    if not config.BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN not set — see .env.example")
    if not config.WEBHOOK_SECRET:
        sys.exit("WEBHOOK_SECRET not set — add it to .env first")


def set_webhook(base_url):
    _check()
    url = base_url.rstrip("/") + f"/webhook/{config.WEBHOOK_SECRET}"
    resp = requests.post(
        f"{_API}/setWebhook",
        data={
            "url": url,
            "secret_token": config.WEBHOOK_SECRET,
            "drop_pending_updates": "true",
        },
        timeout=30,
    )
    print(resp.status_code, resp.text)
    print("Registered webhook:", url)


def delete_webhook():
    _check()
    resp = requests.post(f"{_API}/deleteWebhook", timeout=30)
    print(resp.status_code, resp.text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python set_webhook.py https://<user>.pythonanywhere.com   (or --delete)")
    if sys.argv[1] == "--delete":
        delete_webhook()
    else:
        set_webhook(sys.argv[1])
