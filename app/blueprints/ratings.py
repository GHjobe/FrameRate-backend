"""Ratings and the top-rated list, for example /api/movies/top-rated. Owner: Dev 5 (DATA-01, DATA-02)."""
from flask import Blueprint

bp = Blueprint("ratings", __name__, url_prefix="/api")