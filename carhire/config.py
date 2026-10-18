"""Application settings."""
import os


class Config:
    # Used by Flask to sign the session cookie (flash messages).
    SECRET_KEY = "carhire-dev-secret-2026"

    # Optional fixed "current date/time" so results are repeatable,
    # e.g. CARHIRE_NOW=2026-11-01T09:00. When unset, the real clock is used.
    FIXED_NOW = os.environ.get("CARHIRE_NOW")
