from datetime import timedelta, timezone

import requests
from flask import current_app

from app.extensions import db
from app.models.base import utcnow
from app.models.movie import Movie
from app.models.movie_stats import MovieStats


class TMDBError(Exception):
    def __init__(self, code, message, status):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# TMDB genre ids to names. "Sci-Fi" is the name the frontend uses.
GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}


def _get(path, params=None):
    """The only function that talks to TMDB. It reads the token from the config, never sends it
    anywhere else, and turns every failure into a TMDBError."""
    token = current_app.config.get("TMDB_READ_TOKEN")
    if not token:
        raise TMDBError("TMDB_NOT_CONFIGURED", "The movie service is not set up yet.", 503)
    try:
        response = requests.get(
            current_app.config["TMDB_BASE_URL"] + path,
            params=params,
            headers={"Authorization": f"Bearer {token}", "accept": "application/json"},
            timeout=current_app.config["TMDB_TIMEOUT"],
        )
    except requests.RequestException:
        raise TMDBError("TMDB_UNAVAILABLE", "The movie service is not reachable right now.", 503) from None
    if response.status_code == 404:
        raise TMDBError("MOVIE_NOT_FOUND", "Movie not found.", 404)
    if response.status_code != 200:
        current_app.logger.warning("TMDB answered %s for %s", response.status_code, path)
        raise TMDBError("TMDB_UNAVAILABLE", "The movie service is not available right now.", 503)
    try:
        return response.json()
    except ValueError:
        raise TMDBError("TMDB_UNAVAILABLE", "The movie service sent an unreadable answer.", 503) from None


def _year(release_date):
    try:
        return int((release_date or "")[:4])
    except ValueError:
        return None


def _save(data, detailed):
    """Create or update a row in the movies table. Search results are partial (no runtime), so only
    a detail fetch sets runtime and fetched_at. runtime = None means details were never fetched."""
    movie = db.session.get(Movie, data["id"])
    if movie is None:
        movie = Movie(tmdb_id=data["id"], title=data.get("title") or "Untitled")
        db.session.add(movie)
    movie.title = data.get("title") or movie.title
    movie.year = _year(data.get("release_date"))
    movie.overview = data.get("overview") or None
    movie.poster_path = data.get("poster_path")
    movie.backdrop_path = data.get("backdrop_path")
    if "genres" in data:  # detail answers send [{"id": 28, "name": "Action"}]
        movie.genres = [GENRES.get(g["id"], g["name"]) for g in data["genres"]]
    else:  # search answers send [28, 878]
        movie.genres = [GENRES[i] for i in data.get("genre_ids", []) if i in GENRES]
    if detailed:
        movie.runtime = data.get("runtime") or 0
        movie.fetched_at = utcnow()
    return movie


def _is_fresh(movie):
    if movie.runtime is None:  # only seen in search results so far
        return False
    fetched = movie.fetched_at
    if fetched.tzinfo is None:  # SQLite gives back datetimes without a timezone
        fetched = fetched.replace(tzinfo=timezone.utc)
    return utcnow() - fetched < timedelta(days=current_app.config["MOVIE_CACHE_DAYS"])


def movie_to_public(movie):
    """The movie object the frontend expects (same fields as its mock movies)."""
    base = current_app.config["TMDB_IMAGE_BASE"]
    stats = db.session.get(MovieStats, movie.tmdb_id)
    votes = (stats.total_votes or 0) if stats else 0
    return {
        "id": movie.tmdb_id,
        "title": movie.title,
        "year": movie.year,
        "runtime": movie.runtime or None,
        "synopsis": movie.overview or "",
        "poster": f"{base}/w500{movie.poster_path}" if movie.poster_path else "",
        "backdrop": f"{base}/w1280{movie.backdrop_path}" if movie.backdrop_path else "",
        "genres": movie.genres or [],
        "score": round(stats.bayesian_rating or 0, 2) if votes else None,
        "ratings": votes,
    }


def get_or_fetch_movie(tmdb_id):
    """Return the Movie row for a TMDB id, fetching it from TMDB if it is missing or stale.
    Dev 5: call this before saving a rating or watchlist entry, so the movie row exists."""
    movie = db.session.get(Movie, tmdb_id)
    if movie is not None and _is_fresh(movie):
        return movie
    try:
        data = _get(f"/movie/{tmdb_id}")
    except TMDBError as error:
        if movie is not None and error.code != "MOVIE_NOT_FOUND":
            return movie  # TMDB is down: serve what we already have
        raise
    movie = _save(data, detailed=True)
    db.session.commit()
    return movie


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_movies(query, page=1):
    try:
        data = _get("/search/movie", {"query": query, "page": page, "include_adult": "false"})
    except TMDBError:
        # TMDB is unreachable: fall back to movies we have already cached.
        rows = (
            db.session.query(Movie)
            .filter(Movie.title.ilike(f"%{_escape_like(query)}%", escape="\\"))
            .order_by(Movie.title)
            .limit(20)
            .all()
        )
        if not rows:
            raise
        return {
            "results": [movie_to_public(m) for m in rows],
            "page": 1, "totalPages": 1, "totalResults": len(rows), "cached": True,
        }
    movies = [_save(item, detailed=False) for item in data.get("results", []) if item.get("id")]
    db.session.commit()
    return {
        "results": [movie_to_public(m) for m in movies],
        "page": data.get("page", page),
        "totalPages": min(data.get("total_pages", 1), 500),
        "totalResults": data.get("total_results", len(movies)),
        "cached": False,
    }