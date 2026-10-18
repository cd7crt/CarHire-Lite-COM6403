"""SQLite connection handling and database initialisation."""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def get_db():
    """Return the database connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Drop and recreate all tables, then load the sample cars."""
    conn = get_db()
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.commit()


@click.command("init-db")
def init_db_command():
    """Reset the database to its starting state."""
    init_db()
    click.echo("Database reset: 8 sample cars, no bookings.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    # Create the database automatically the first time the app starts.
    if not Path(app.config["DATABASE"]).exists():
        with app.app_context():
            init_db()
