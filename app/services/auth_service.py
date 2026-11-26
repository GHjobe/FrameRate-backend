"""User database work for the auth routes (API-04).

The routes in blueprints/auth.py only read the request, call these functions and build the
response. Everything that touches the users table lives here."""
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.utils.security import hash_password, verify_password


class DuplicateUserError(Exception):
    """The username or email was taken by someone else at the same moment."""


def find_taken_fields(username, email):
    """Return a message for each of username and email that is already in use (ignoring case)."""
    taken = {}
    if db.session.query(User.id).filter(func.lower(User.username) == username.lower()).first():
        taken["username"] = "That username is already taken."
    if db.session.query(User.id).filter(func.lower(User.email) == email.lower()).first():
        taken["email"] = "That email is already registered."
    return taken


def create_user(username, email, password):
    """Hash the password and save a new user. Raises DuplicateUserError if the name is taken."""
    user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # two people registering the same name at the same moment
        db.session.rollback()
        raise DuplicateUserError from None
    return user


def authenticate(identifier, password):
    """Return the user when the email or username and the password match, otherwise None."""
    identifier = identifier.lower()
    user = (
        db.session.query(User)
        .filter(or_(func.lower(User.email) == identifier, func.lower(User.username) == identifier))
        .first()
    )
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def get_user(user_id):
    """Return the user with this id, or None when there is no id or no such user."""
    return db.session.get(User, user_id) if user_id else None