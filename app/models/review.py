from sqlalchemy import false

from ..extensions import db
from .base import utcnow


class Review(db.Model):
    """An optional written review. It belongs to a rating, so a user has at most one per movie."""

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    rating_id = db.Column(db.Integer, db.ForeignKey("ratings.id", ondelete="CASCADE"), nullable=False, unique=True)
    body = db.Column(db.Text, nullable=False)
    contains_spoiler = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    is_hidden = db.Column(db.Boolean, nullable=False, default=False, server_default=false())  # set by moderators
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (db.CheckConstraint("length(trim(body)) > 0", name="body_not_blank"),)

    rating = db.relationship("Rating", back_populates="review")