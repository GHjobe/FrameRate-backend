"""Authentication routes: register, login, logout, me. Owner: Dev 3 (API-04).

Login is a Flask session cookie that stores the user's id under the key "user_id".
Dev 4 (SEC-03): read session["user_id"] in @login_required.

Hashing and the password policy come from Dev 4's app/utils/security.py. The username and
email checks below are kept here until app/utils/errors.py (SEC-02) is on main, so that
validate_register and validate_login from app/utils/validators.py can replace them."""
import re

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.api_errors import api_error
from app.extensions import db
from app.models import User
from app.utils.security import check_password_policy, hash_password, verify_password

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")  # 20 matches the users.username column
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---- input checks ---------------------------------------------------------------

def _password_problem(password):
    if not password:
        return "Password is required."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    problems = check_password_policy(password)
    return " ".join(problems) if problems else None


def _validation_error(fields):
    return api_error("VALIDATION", "Please fix the highlighted fields.", 400, fields)


# ---- helpers --------------------------------------------------------------------

def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _text(data, key):
    value = data.get(key)
    return value if isinstance(value, str) else ""


def _sign_in(user):
    session.clear()  # start a fresh session so an old one cannot be reused
    session["user_id"] = user.id
    session.permanent = True


# ---- routes ---------------------------------------------------------------------

@bp.post("/register")
def register():
    data = _json_body()
    if data is None:
        return api_error("VALIDATION", "Send the form as JSON.", 400)

    username = _text(data, "username").strip()
    email = _text(data, "email").strip().lower()
    password = _text(data, "password")

    fields = {}
    if not USERNAME_RE.match(username):
        fields["username"] = "Use 3 to 20 letters, numbers or underscores."
    if len(email) > 254 or not EMAIL_RE.match(email):
        fields["email"] = "Enter a valid email address."
    problem = _password_problem(password)
    if problem:
        fields["password"] = problem
    if fields:
        return _validation_error(fields)

    taken = {}
    if db.session.query(User.id).filter(func.lower(User.username) == username.lower()).first():
        taken["username"] = "That username is already taken."
    if db.session.query(User.id).filter(func.lower(User.email) == email).first():
        taken["email"] = "That email is already registered."
    if taken:
        return api_error("CONFLICT", "Some details are already in use.", 409, taken)

    user = User(username=username, email=email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:  # two people registering the same name at the same moment
        db.session.rollback()
        return api_error("CONFLICT", "That username or email is already in use.", 409)

    _sign_in(user)
    return jsonify(user.to_public()), 201


@bp.post("/login")
def login():
    data = _json_body()
    if data is None:
        return api_error("VALIDATION", "Send the form as JSON.", 400)

    # The frontend can send the email or the username, in any of these fields.
    identifier = (_text(data, "email") or _text(data, "username") or _text(data, "identifier")).strip().lower()
    password = _text(data, "password")

    fields = {}
    if not identifier:
        fields["email"] = "Enter your email or username."
    if not password:
        fields["password"] = "Enter your password."
    if fields:
        return _validation_error(fields)

    user = (
        db.session.query(User)
        .filter(or_(func.lower(User.email) == identifier, func.lower(User.username) == identifier))
        .first()
    )
    # One message for "no such user" and "wrong password", so nobody can probe which accounts exist.
    if user is None or not verify_password(password, user.password_hash):
        return api_error("INVALID_CREDENTIALS", "Wrong email or password.", 401)

    _sign_in(user)
    return jsonify(user.to_public())


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/me")
def me():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if user is None:
        session.clear()
        return api_error("UNAUTHENTICATED", "You are not logged in.", 401)
    return jsonify(user.to_public())