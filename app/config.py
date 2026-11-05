import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # the backend/ folder
load_dotenv(BASE_DIR / ".env")


def _origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


class Config:
    # Set a real SECRET_KEY in backend/.env. The fallback only keeps local development working.
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-only-secret-change-me"

    # A relative sqlite path is stored in backend/instance/ (ignored by Git).
    # To move to Postgres later, only this value in .env changes.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///framerate.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = _origins()
    MIGRATIONS_DIR = str(BASE_DIR / "migrations")

    # Read by the TMDB wrapper (API-03). Never sent to the frontend.
    TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN", "")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"