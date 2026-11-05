from flask import Flask
from flask_cors import CORS

from .blueprints import register_blueprints
from .config import Config
from .extensions import db, migrate

# API-02 adds `from . import models` here so every table is registered with the migrations.


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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