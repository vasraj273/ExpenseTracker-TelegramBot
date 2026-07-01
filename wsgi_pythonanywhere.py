# Sample WSGI config for PythonAnywhere.
#
# On PythonAnywhere: Web tab -> your web app -> "WSGI configuration file".
# Replace its contents with the lines below. Set PROJECT_PATH to the folder
# where you cloned the repo (run `pwd` inside it to confirm the exact path).

import sys

PROJECT_PATH = "/home/ShyPurr/ExpenseTracker-TelegramBot"

if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

from flask_app import app as application  # noqa: E402
