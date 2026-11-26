"""Authentication routes: register, login, logout, me. Owner: Dev 3 (API-04).

These routes only handle the web request: read the data, check it, call app/services/
auth_service.py for anything that touches the database, and build the response.

Login is a Flask session cookie that stores the user's id under the key "user_id".
Dev 4 (SEC-03): read session["user_id"] in @login_required.

The password policy comes from Dev 4's app/utils/security.py. The username and email checks
below are kept here until app/utils/errors.py (SEC-02) is on main, so that validate_register
and validate_login from app/utils/validators.py can replace them."""
import re

from flask import Blueprint, jsonify, request, session

from app.api_errors import api_error
from app.services.auth_service import (
    DuplicateUserError,
    authenticate,
    create_user,
    find_taken_fields,
    get_user,
)
from app.utils.security import check_password_policy

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

    taken = find_taken_fields(username, email)
    if taken:
        return api_error("CONFLICT", "Some details are already in use.", 409, taken)

    try:
        user = create_user(username, email, password)
    except DuplicateUserError:  # two people registering the same name at the same moment
        return api_error("CONFLICT", "That username or email is already in use.", 409)

    _sign_in(user)
    return jsonify(user.to_public()), 201


@bp.post("/login")
def login():
    data = _json_body()
    if data is None:
        return api_error("VALIDATION", "Send the form as JSON.", 400)

    # The frontend can send the email or the username, in any of these fields.
    identifier = (_text(data, "email") or _text(data, "username") or _text(data, "identifier")).strip()
    password = _text(data, "password")

    fields = {}
    if not identifier:
        fields["email"] = "Enter your email or username."
    if not password:
        fields["password"] = "Enter your password."
    if fields:
        return _validation_error(fields)

    user = authenticate(identifier, password)
    # One message for "no such user" and "wrong password", so nobody can probe which accounts exist.
    if user is None:
        return api_error("INVALID_CREDENTIALS", "Wrong email or password.", 401)

    _sign_in(user)
    return jsonify(user.to_public())


@bp.post("/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/me")
def me():
    user = get_user(session.get("user_id"))
    if user is None:
        session.clear()
        return api_error("UNAUTHENTICATED", "You are not logged in.", 401)
    return jsonify(user.to_public())