import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask_migrate import upgrade
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Movie, Rating, User


def make_file_app(tmp_path):
    class FileConfig(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'migration_test.db'}"

    return create_app(FileConfig)


def test_migrations_create_every_table(tmp_path):
    app = make_file_app(tmp_path)
    with app.app_context():
        upgrade()
        created = set(inspect(db.engine).get_table_names())
        db.engine.dispose()
    assert set(db.metadata.tables) <= created


def test_models_and_migrations_are_in_sync(tmp_path):
    """Fails when someone changes a model but forgets `flask db migrate` (and commits the file)."""
    app = make_file_app(tmp_path)
    with app.app_context():
        upgrade()
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection, opts={"compare_type": False})
            differences = compare_metadata(context, db.metadata)
        db.engine.dispose()
    assert differences == [], f"models and migrations differ: {differences}"


def test_a_migrated_database_enforces_the_same_rules_as_the_models(tmp_path):
    """The comparison above cannot see expression indexes on SQLite, and the other tests build
    their tables with create_all. This one checks the rules on a database built by the migration."""
    app = make_file_app(tmp_path)
    with app.app_context():
        upgrade()

        def refused(obj):
            db.session.add(obj)
            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

        db.session.add_all([
            User(username="Demo", email="demo@example.com", password_hash="x"),
            Movie(tmdb_id=1, title="Inception"),
        ])
        db.session.commit()
        user = db.session.query(User).one()

        refused(User(username="demo", email="new@example.com", password_hash="x"))    # username, ignoring case
        refused(User(username="new", email="DEMO@example.com", password_hash="x"))    # email, ignoring case
        refused(Rating(user_id=user.id, tmdb_id=1, score=9))                          # score out of range

        db.session.add(Rating(user_id=user.id, tmdb_id=1, score=5))
        db.session.commit()
        refused(Rating(user_id=user.id, tmdb_id=1, score=4))                          # second rating, same movie

        db.session.remove()
        db.engine.dispose()