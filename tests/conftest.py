import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Movie, User


@pytest.fixture()
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    counter = {"n": 0}

    def _make(**overrides):
        counter["n"] += 1
        n = counter["n"]
        values = {"username": f"user{n}", "email": f"user{n}@example.com", "password_hash": "not-a-real-hash"}
        values.update(overrides)
        user = User(**values)
        db.session.add(user)
        db.session.commit()
        return user

    return _make


@pytest.fixture()
def make_movie(app):
    def _make(tmdb_id=27205, title="Inception", **overrides):
        movie = Movie(tmdb_id=tmdb_id, title=title, **overrides)
        db.session.add(movie)
        db.session.commit()
        return movie

    return _make