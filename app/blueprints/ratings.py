"""Ratings and the top-rated list, for example /api/movies/top-rated. Owner: Dev 5 (DATA-01, DATA-02)."""
from flask import Blueprint, jsonify, request, session

from app.api_errors import api_error
from app.extensions import db
from app.models.movie import Movie
from app.models.movie_stats import MovieStats
from app.models.rating import Rating
from app.services.stats_service import update_movie_score
from app.services.tmdb import get_or_fetch_movie

bp = Blueprint("ratings", __name__, url_prefix="/api")


def _serialize_rating(rating):
    return {
        "id": rating.id,
        "user_id": rating.user_id,
        "tmdb_id": rating.tmdb_id,
        "score": rating.score,
        "status": rating.status,
        "created_at": rating.created_at.isoformat(),
        "updated_at": rating.updated_at.isoformat(),
    }


@bp.route("/movies/top-rated", methods=["GET"])
def get_top_rated():
    movies = (
        db.session.query(Movie, MovieStats)
        .join(MovieStats, Movie.tmdb_id == MovieStats.movie_id)
        .order_by(MovieStats.bayesian_rating.desc())
        .limit(20)
        .all()
    )
    data = [
        {"id": m.tmdb_id, "title": m.title, "score": s.bayesian_rating, "votes": s.total_votes}
        for m, s in movies
    ]
    return jsonify(data), 200


@bp.route("/movies/<int:tmdb_id>/rating", methods=["PUT"])
def put_rating(tmdb_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Authentication required.", 401)

    # Validate whole integer score (1-5)
    score = (request.get_json(silent=True) or {}).get("score")
    if not isinstance(score, int) or isinstance(score, bool) or not (1 <= score <= 5):
        return api_error("VALIDATION_ERROR", "Score must be an integer from 1 to 5.", 400, fields={"score": "Must be 1 to 5."})

    # Ensure movie exists in local cache
    if not get_or_fetch_movie(tmdb_id):
        return api_error("NOT_FOUND", "Movie not found.", 404)

    # Update existing rating or create a new one
    rating = Rating.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()
    if rating:
        rating.score = score
        status_code = 200
    else:
        rating = Rating(user_id=user_id, tmdb_id=tmdb_id, score=score)
        db.session.add(rating)
        status_code = 201

    db.session.commit()
    update_movie_score(tmdb_id)
    return jsonify(_serialize_rating(rating)), status_code


@bp.route("/movies/<int:tmdb_id>/rating", methods=["DELETE"])
def delete_rating(tmdb_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Authentication required.", 401)

    rating = Rating.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()
    if not rating:
        return api_error("NOT_FOUND", "Rating not found.", 404)

    db.session.delete(rating)
    db.session.commit()
    update_movie_score(tmdb_id)
    return jsonify({"message": "Rating deleted."}), 200