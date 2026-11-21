from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from . import models  # noqa: F401  (registers every table with SQLAlchemy and the migrations)
from .blueprints import register_blueprints
from .config import Config, check_settings
from .extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config["TESTING"]:
        check_settings(app.config)

    # How long a login lasts, in days (from .env).
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=app.config["SESSION_LIFETIME_DAYS"])

    db.init_app(app)
    migrate.init_app(app, db, directory=app.config["MIGRATIONS_DIR"], render_as_batch=True)

    # Only the frontend's origins may call /api, and cookies are allowed (needed for login sessions).
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    register_blueprints(app)

    # Dev 4 (SEC-02): call register_error_handlers(app) and setup_logging(app) here.

    return app