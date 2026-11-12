from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models import Movie
from app.services import tmdb

INCEPTION = {
    "id": 27205, "title": "Inception", "release_date": "2010-07-15", "runtime": 148,
    "overview": "A thief who steals secrets through dreams.",
    "poster_path": "/p.jpg", "backdrop_path": "/b.jpg",
    "genres": [{"id": 878, "name": "Science Fiction"}, {"id": 28, "name": "Action"}],
}
SEARCH_HIT = {
    "id": 27205, "title": "Inception", "release_date": "2010-07-15",
    "overview": "A thief who steals secrets through dreams.",
    "poster_path": "/p.jpg", "backdrop_path": "/b.jpg", "genre_ids": [28, 878],
}


@pytest.fixture()
def fake_tmdb(monkeypatch):
    """Replaces the one function that talks to TMDB, so tests never use the network."""
    calls = []

    def fake_get(path, params=None):
        calls.append(path)
        if path == "/search/movie":
            return {"page": 1, "total_pages": 1, "total_results": 1, "results": [SEARCH_HIT]}
        if path == "/movie/27205":
            return INCEPTION
        raise tmdb.TMDBError("MOVIE_NOT_FOUND", "Movie not found.", 404)

    monkeypatch.setattr(tmdb, "_get", fake_get)
    return calls


def tmdb_down(monkeypatch):
    def down(path, params=None):
        raise tmdb.TMDBError("TMDB_UNAVAILABLE", "down", 503)

    monkeypatch.setattr(tmdb, "_get", down)


def test_details_have_the_frontend_shape_and_are_cached(client, fake_tmdb):
    response = client.get("/api/movies/27205")
    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == 27205
    assert body["title"] == "Inception"
    assert body["year"] == 2010
    assert body["runtime"] == 148
    assert body["synopsis"].startswith("A thief")
    assert body["poster"] == "https://image.tmdb.org/t/p/w500/p.jpg"
    assert body["genres"] == ["Sci-Fi", "Action"]
    assert body["score"] is None and body["ratings"] == 0
    assert db.session.get(Movie, 27205) is not None

    client.get("/api/movies/27205")
    assert fake_tmdb == ["/movie/27205"]  # the second request came from the cache


def test_search_saves_results_and_details_fetch_the_rest(client, fake_tmdb):
    response = client.get("/api/movies/search?q=inception")
    body = response.get_json()
    assert response.status_code == 200
    assert body["results"][0]["id"] == 27205
    assert body["results"][0]["genres"] == ["Action", "Sci-Fi"]
    assert body["cached"] is False
    assert db.session.get(Movie, 27205).runtime is None  # partial row

    client.get("/api/movies/27205")
    assert fake_tmdb == ["/search/movie", "/movie/27205"]
    assert db.session.get(Movie, 27205).runtime == 148


def test_empty_search_returns_nothing_without_calling_tmdb(client, fake_tmdb):
    response = client.get("/api/movies/search?q=   ")
    assert response.status_code == 200
    assert response.get_json()["results"] == []
    assert fake_tmdb == []


@pytest.mark.parametrize("page", ["0", "abc", "501"])
def test_search_rejects_a_bad_page(client, fake_tmdb, page):
    response = client.get(f"/api/movies/search?q=x&page={page}")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION"


def test_unknown_movie_is_a_404(client, fake_tmdb):
    response = client.get("/api/movies/999")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "MOVIE_NOT_FOUND"


def test_missing_token_is_a_clear_503(app, client):
    app.config["TMDB_READ_TOKEN"] = ""
    response = client.get("/api/movies/27205")
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "TMDB_NOT_CONFIGURED"


def test_stale_cache_is_served_when_tmdb_is_down(client, make_movie, monkeypatch):
    old = datetime.now(timezone.utc) - timedelta(days=30)
    make_movie(tmdb_id=27205, title="Inception", runtime=148, genres=["Sci-Fi"], fetched_at=old)
    tmdb_down(monkeypatch)
    response = client.get("/api/movies/27205")
    assert response.status_code == 200
    assert response.get_json()["title"] == "Inception"


def test_search_uses_the_cache_when_tmdb_is_down(client, make_movie, monkeypatch):
    make_movie(tmdb_id=27205, title="Inception", runtime=148)
    tmdb_down(monkeypatch)
    response = client.get("/api/movies/search?q=incep")
    assert response.status_code == 200
    body = response.get_json()
    assert body["cached"] is True
    assert body["results"][0]["id"] == 27205
    assert client.get("/api/movies/search?q=zzz").status_code == 503  # nothing cached to fall back on