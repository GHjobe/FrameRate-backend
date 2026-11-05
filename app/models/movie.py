from ..extensions import db
from .base import utcnow


class Movie(db.Model):
    """A cache of TMDB details, keyed by the TMDB id. Refresh rows by updating them, never delete
    them: ratings, reviews, and watchlist entries point here."""

    __tablename__ = "movies"

    tmdb_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.Integer)
    runtime = db.Column(db.Integer)  # minutes
    overview = db.Column(db.Text)  # the frontend calls this "synopsis"
    poster_path = db.Column(db.String(255))
    backdrop_path = db.Column(db.String(255))
    genres = db.Column(db.JSON, nullable=False, default=list)  # for example ["Sci-Fi", "Action"]
    fetched_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)