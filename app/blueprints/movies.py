"""Movie search and details (TMDB wrapper). Owner: Dev 3 (API-03)."""
from flask import Blueprint, jsonify, request

from app.api_errors import api_error
from app.services.tmdb import TMDBError, get_or_fetch_movie, movie_to_public, search_movies

bp = Blueprint("movies", __name__, url_prefix="/api/movies")


@bp.get("/search")
def search_route():
    query = request.args.get("q", "").strip()
    if len(query) > 100:
        return api_error("VALIDATION", "Search term is too long.", 400, {"q": "Use 100 characters or fewer."})
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 0
    if not 1 <= page <= 500:
        return api_error("VALIDATION", "Invalid page number.", 400, {"page": "Use a number from 1 to 500."})
    if not query:
        return jsonify(results=[], page=1, totalPages=0, totalResults=0, cached=False)
    try:
        return jsonify(search_movies(query, page))
    except TMDBError as error:
        return api_error(error.code, error.message, error.status)


@bp.get("/<int:tmdb_id>")
def movie_details(tmdb_id):
    try:
        movie = get_or_fetch_movie(tmdb_id)
    except TMDBError as error:
        return api_error(error.code, error.message, error.status)
    return jsonify(movie_to_public(movie))