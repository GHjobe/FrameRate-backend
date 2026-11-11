"""Ratings and the top-rated list, for example /api/movies/top-rated. Owner: Dev 5 (DATA-01, DATA-02)."""
from flask import Blueprint, jsonify
from app.extensions import db
from app.models.movie import Movie
from app.models.movie_stats import MovieStats

bp = Blueprint("ratings", __name__, url_prefix="/api")

@bp.route('/movies/top-rated', methods=['GET'])
def get_top_rated():
    movies = db.session.query(Movie, MovieStats).join(
        MovieStats, Movie.tmdb_id == MovieStats.movie_id
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