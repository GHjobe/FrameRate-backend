from ..extensions import db
from .base import in_list, utcnow

# The four statuses from the DATA-04 ticket; 'plan' also matches the frontend mocks.
WATCHLIST_STATUSES = ("plan", "watched", "on_hold", "dropped")


class WatchlistItem(db.Model):
    __tablename__ = "watchlist"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey("movies.tmdb_id", ondelete="RESTRICT"), primary_key=True)
    status = db.Column(db.String(16), nullable=False, default="plan", server_default="plan")
    added_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)  # "dateAdded" in the frontend
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (db.CheckConstraint(in_list("status", WATCHLIST_STATUSES), name="status_valid"),)

    user = db.relationship("User", back_populates="watchlist_items")
    movie = db.relationship("Movie")