from .auth import bp as auth_bp
from .health import bp as health_bp
from .moderation import bp as moderation_bp
from .movies import bp as movies_bp
from .preferences import bp as preferences_bp
from .ratings import bp as ratings_bp
from .reviews import bp as reviews_bp
from .watchlist import bp as watchlist_bp


def register_blueprints(app):
    for blueprint in (
        health_bp,
        auth_bp,
        movies_bp,
        ratings_bp,
        reviews_bp,
        watchlist_bp,
        preferences_bp,
        moderation_bp,
    ):
        app.register_blueprint(blueprint)