import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Movie, Rating, Review, User, UserPreferences, WatchlistItem


def commit_fails():
    """Run the pending changes and expect the database to refuse them."""
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


# ---- users ---------------------------------------------------------------

def test_user_defaults_and_public_shape(make_user):
    user = make_user(username="marc", email="marc@example.com")
    assert user.role == "user"
    assert user.email_verified is False
    assert user.onboarding_completed is False
    assert user.created_at is not None
    assert user.to_public() == {
        "id": user.id,
        "username": "marc",
        "email": "marc@example.com",
        "role": "user",
        "emailVerified": False,
        "onboardingCompleted": False,
    }
    assert "password" not in str(user.to_public()).lower()


def test_username_and_email_are_unique_ignoring_case(make_user):
    make_user(username="Demo", email="demo@example.com")
    db.session.add(User(username="demo", email="other@example.com", password_hash="x"))
    commit_fails()
    db.session.add(User(username="other", email="DEMO@example.com", password_hash="x"))
    commit_fails()


def test_unknown_role_is_rejected(make_user):
    db.session.add(User(username="x1", email="x1@example.com", password_hash="x", role="superhero"))
    commit_fails()


# ---- ratings -------------------------------------------------------------

def test_one_rating_per_user_per_movie(make_user, make_movie):
    user, movie = make_user(), make_movie()
    db.session.add(Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=4))
    db.session.commit()
    db.session.add(Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=5))
    commit_fails()


@pytest.mark.parametrize("bad_score", [0, 6, -1])
def test_rating_score_must_be_1_to_5(make_user, make_movie, bad_score):
    user, movie = make_user(), make_movie()
    db.session.add(Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=bad_score))
    commit_fails()


def test_rating_defaults_to_active_and_rejects_unknown_status(make_user, make_movie):
    user, movie = make_user(), make_movie()
    rating = Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=3)
    db.session.add(rating)
    db.session.commit()
    assert rating.status == "active"

    rating.status = "banana"
    commit_fails()


def test_rating_must_point_to_an_existing_movie(make_user):
    user = make_user()
    db.session.add(Rating(user_id=user.id, tmdb_id=999999, score=4))
    commit_fails()


def test_a_movie_with_ratings_cannot_be_deleted(make_user, make_movie):
    user, movie = make_user(), make_movie()
    db.session.add(Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=4))
    db.session.commit()
    with pytest.raises(IntegrityError):
        db.session.execute(delete(Movie).where(Movie.tmdb_id == movie.tmdb_id))
    db.session.rollback()


# ---- reviews -------------------------------------------------------------

def make_rating(user, movie, score=4):
    rating = Rating(user_id=user.id, tmdb_id=movie.tmdb_id, score=score)
    db.session.add(rating)
    db.session.commit()
    return rating


def test_review_defaults_and_one_review_per_rating(make_user, make_movie):
    rating = make_rating(make_user(), make_movie())
    review = Review(rating_id=rating.id, body="Great film.")
    db.session.add(review)
    db.session.commit()
    assert review.contains_spoiler is False
    assert review.is_hidden is False
    assert rating.review.body == "Great film."

    db.session.add(Review(rating_id=rating.id, body="Second review"))
    commit_fails()


def test_review_body_cannot_be_blank(make_user, make_movie):
    rating = make_rating(make_user(), make_movie())
    db.session.add(Review(rating_id=rating.id, body="   "))
    commit_fails()


def test_deleting_a_rating_removes_its_review_in_the_database(make_user, make_movie):
    rating = make_rating(make_user(), make_movie())
    db.session.add(Review(rating_id=rating.id, body="Gone with the rating."))
    db.session.commit()

    db.session.execute(delete(Rating).where(Rating.id == rating.id))  # plain SQL, no ORM help
    db.session.commit()
    assert db.session.query(Review).count() == 0


def test_deleting_a_user_removes_their_data(make_user, make_movie):
    user, movie = make_user(), make_movie()
    make_rating(user, movie)
    db.session.add(WatchlistItem(user_id=user.id, tmdb_id=movie.tmdb_id))
    db.session.add(UserPreferences(user_id=user.id))
    db.session.commit()

    db.session.delete(user)
    db.session.commit()
    assert db.session.query(Rating).count() == 0
    assert db.session.query(WatchlistItem).count() == 0
    assert db.session.query(UserPreferences).count() == 0
    assert db.session.query(Movie).count() == 1  # the movie cache stays


# ---- watchlist and preferences ------------------------------------------

def test_watchlist_defaults_and_valid_statuses(make_user, make_movie):
    user, movie = make_user(), make_movie()
    item = WatchlistItem(user_id=user.id, tmdb_id=movie.tmdb_id)
    db.session.add(item)
    db.session.commit()
    assert item.status == "plan"
    assert item.added_at is not None

    for status in ("watched", "on_hold", "dropped"):
        item.status = status
        db.session.commit()

    item.status = "someday"
    commit_fails()


def test_a_movie_can_be_on_a_users_watchlist_only_once(make_user, make_movie):
    user, movie = make_user(), make_movie()
    db.session.add(WatchlistItem(user_id=user.id, tmdb_id=movie.tmdb_id))
    db.session.commit()
    db.session.add(WatchlistItem(user_id=user.id, tmdb_id=movie.tmdb_id))
    commit_fails()


def test_preferences_defaults(make_user):
    user = make_user()
    prefs = UserPreferences(user_id=user.id)
    db.session.add(prefs)
    db.session.commit()
    assert prefs.region == "PH"
    assert prefs.language == "en"
    assert prefs.blur_spoilers is True
    assert prefs.genres == []
    assert prefs.services == []


def test_movie_stores_genres_as_a_list(make_movie):
    movie = make_movie(genres=["Sci-Fi", "Action"], year=2010, runtime=148)
    db.session.expire_all()
    assert db.session.get(Movie, movie.tmdb_id).genres == ["Sci-Fi", "Action"]