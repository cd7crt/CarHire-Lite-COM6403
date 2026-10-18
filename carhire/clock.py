"""Single source of the current date/time for the whole application."""
from datetime import datetime

from flask import current_app


def now():
    """Return the current date/time, or the fixed time set in FIXED_NOW."""
    fixed = current_app.config.get("FIXED_NOW")
    if fixed:
        return datetime.fromisoformat(fixed)
    return datetime.now().replace(second=0, microsecond=0)
