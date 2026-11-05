from sqlalchemy import true

from ..extensions import db


class UserPreferences(db.Model):
    """What the onboarding page collects. Same field names as the frontend's preferences store."""

    __tablename__ = "user_preferences"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    region = db.Column(db.String(2), nullable=False, default="PH", server_default="PH")
    language = db.Column(db.String(8), nullable=False, default="en", server_default="en")
    blur_spoilers = db.Column(db.Boolean, nullable=False, default=True, server_default=true())
    genres = db.Column(db.JSON, nullable=False, default=list)    # for example ["Action", "Drama", "Comedy"]
    services = db.Column(db.JSON, nullable=False, default=list)  # for example ["netflix", "prime"]

    user = db.relationship("User", back_populates="preferences")