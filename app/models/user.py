from sqlalchemy import false

from ..extensions import db
from .base import in_list, utcnow

ROLES = ("user", "moderator", "admin")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)  # 3 to 20 characters, checked by the validators
    email = db.Column(db.String(254), nullable=False)    # store lowercase
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="user", server_default="user")
    email_verified = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False, server_default=false())
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    __table_args__ = (db.CheckConstraint(in_list("role", ROLES), name="role_valid"),)

    ratings = db.relationship("Rating", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    watchlist_items = db.relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    preferences = db.relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )

    def to_public(self):
        """The user object the frontend expects. Never includes the password hash."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "emailVerified": self.email_verified,
            "onboardingCompleted": self.onboarding_completed,
        }


# "Demo" and "demo" must count as the same username, and so must emails.
db.Index("uq_users_username_lower", db.func.lower(User.username), unique=True)
db.Index("uq_users_email_lower", db.func.lower(User.email), unique=True)