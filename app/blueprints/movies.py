"""Movie search and details (TMDB wrapper). Owner: Dev 3 (API-03)."""
from flask import Blueprint

bp = Blueprint("movies", __name__, url_prefix="/api/movies")

from flask import jsonify
from app.models.base import db
from app.models.movie import Movie
from app.models.movie_stats import MovieStats

@bp.route('/top-rated', methods=['GET'])
def get_top_rated():
    movies = db.session.query(Movie, MovieStats).join(
        MovieStats, Movie.id == MovieStats.movie_id
    ).order_by(MovieStats.bayesian_rating.desc()).limit(20).all()
    
    data = []
    for movie, stats in movies:
        data.append({
            "id": movie.id,
            "title": movie.title,
            "score": stats.bayesian_rating,
            "votes": stats.total_votes
        })
        
    return jsonify(data), 200