"""Authentication routes: register, login, logout, me. Owner: Dev 3 (API-04)."""
from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/api/auth")