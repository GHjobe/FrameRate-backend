import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # the repo root
load_dotenv(BASE_DIR / ".env")


def _origins():
    raw = os.getenv("CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def _int(name):
    """A whole number from .env, or None when the line is missing or not a number."""
    value = os.getenv(name, "")
    return int(value) if value.isdigit() else None


class Config:
    # Every value below comes from .env. There are no fallbacks here: see check_settings().
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    CORS_ORIGINS = _origins()

    # TMDB (API-03). The token is optional at startup; without it the movie routes
    # answer with a clear TMDB_NOT_CONFIGURED error.
    TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")
    TMDB_BASE_URL = os.getenv("TMDB_BASE_URL")
    TMDB_IMAGE_BASE = os.getenv("TMDB_IMAGE_BASE")
    TMDB_TIMEOUT = _int("TMDB_TIMEOUT")  # seconds to wait for TMDB
    MOVIE_CACHE_DAYS = _int("MOVIE_CACHE_DAYS")  # how long cached movie details count as fresh

    # Login sessions (API-04)
    SESSION_LIFETIME_DAYS = _int("SESSION_LIFETIME_DAYS")  # how long a login lasts
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").lower() == "true"  # true only on https

    # Not environment settings: fixed security switches, a framework switch and a computed path.
    SESSION_COOKIE_HTTPONLY = True  # JavaScript cannot read the login cookie
    SESSION_COOKIE_SAMESITE = "Lax"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MIGRATIONS_DIR = str(BASE_DIR / "migrations")


class TestingConfig(Config):
    # Tests must not depend on a developer's .env, so they carry their own fixed values.
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
    TMDB_BASE_URL = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
    TMDB_TIMEOUT = 8
    MOVIE_CACHE_DAYS = 7
    SESSION_LIFETIME_DAYS = 7
    SESSION_COOKIE_SECURE = False


# config setting name -> the line it comes from in .env
REQUIRED_SETTINGS = {
    "SECRET_KEY": "SECRET_KEY",
    "SQLALCHEMY_DATABASE_URI": "DATABASE_URL",
    "CORS_ORIGINS": "CORS_ORIGINS",
    "TMDB_BASE_URL": "TMDB_BASE_URL",
    "TMDB_IMAGE_BASE": "TMDB_IMAGE_BASE",
    "TMDB_TIMEOUT": "TMDB_TIMEOUT",
    "MOVIE_CACHE_DAYS": "MOVIE_CACHE_DAYS",
    "SESSION_LIFETIME_DAYS": "SESSION_LIFETIME_DAYS",
}


def check_settings(config):
    """Stop the app at startup, with a clear message, if .env is incomplete."""
    missing = [env for key, env in REQUIRED_SETTINGS.items() if config.get(key) in (None, "", [])]
    if missing:
        raise RuntimeError(
            "Missing or invalid settings in .env: " + ", ".join(missing)
            + ". Copy the lines from .env.example and fill them in."
        )