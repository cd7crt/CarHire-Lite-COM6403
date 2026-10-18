"""CarHire Lite: a small Flask car-hire booking application."""
import os

from flask import Flask

from . import clock, db
from .api import api_bp
from .web import web_bp


def create_app(test_config=None):
    """Application factory.

    ``test_config`` lets callers override settings, for example::

        create_app({"DATABASE": "/tmp/test.sqlite", "FIXED_NOW": "2026-11-01T09:00"})
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("carhire.config.Config")
    app.config["DATABASE"] = os.path.join(app.instance_path, "carhire.sqlite")
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_now():
        return {"system_now": clock.now()}

    return app
