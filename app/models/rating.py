from ..extensions import db
from .base import in_list, utcnow

RATING_STATUSES = ("active", "quarantined", "removed")


class Rating(db.Model):
    """One star rating (1 to 5, whole stars) per user per movie."""

    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tmdb_id = db.Column(db.Integer, db.ForeignKey("movies.tmdb_id", ondelete="RESTRICT"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    # Rankings only count 'active' ratings. 'quarantined' is for the fake-rating detector (backlog).
    status = db.Column(db.String(16), nullable=False, default="active", server_default="active")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "tmdb_id", name="uq_ratings_user_movie"),
        db.CheckConstraint("score BETWEEN 1 AND 5", name="score_range"),
        db.CheckConstraint(in_list("status", RATING_STATUSES), name="status_valid"),
        db.Index("ix_ratings_tmdb_status", "tmdb_id", "status"),
    )

    user = db.relationship("User", back_populates="ratings")
    movie = db.relationship("Movie")
    review = db.relationship("Review", back_populates="rating", uselist=False, cascade="all, delete-orphan", passive_deletes=True)