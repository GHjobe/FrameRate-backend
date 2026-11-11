"""Movie search and details (TMDB wrapper). Owner: Dev 3 (API-03)."""
from flask import Blueprint

bp = Blueprint("movies", __name__, url_prefix="/api/movies")

from flask import jsonify
from app.extensions import db
from app.models.movie import Movie
from app.models.movie_stats import MovieStats

