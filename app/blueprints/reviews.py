"""Reviews. Owner: Dev 5 (DATA-03)."""
from flask import Blueprint, jsonify, request, session
from app.api_errors import api_error
from app.extensions import db
from app.models.rating import Rating
from app.models.review import Review

bp = Blueprint("reviews", __name__, url_prefix="/api")


def review_to_dict(review):
    return {
        "id": review.id,
        "rating_id": review.rating_id,
        "tmdb_id": review.rating.tmdb_id,
        "user_id": review.rating.user_id,
        "username": review.rating.user.username,
        "score": review.rating.score,
        "body": review.body,
        "contains_spoiler": review.contains_spoiler,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }


@bp.route("/movies/<int:tmdb_id>/reviews", methods=["GET"])
def get_movie_reviews(tmdb_id):
    reviews = (
        Review.query.join(Rating)
        .filter(
            Rating.tmdb_id == tmdb_id,
            Rating.status == "active",
            Review.is_hidden == False,
        )
        .order_by(Review.created_at.desc())
        .all()
    )

    result = []
    for r in reviews:
        result.append(review_to_dict(r))

    return jsonify(result), 200


@bp.route("/movies/<int:tmdb_id>/reviews", methods=["POST"])
def create_review(tmdb_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    rating = Rating.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()
    if not rating:
        return api_error("RATING_REQUIRED", "Rate the movie first before writing a review.", 400)

    if rating.review:
        return api_error("CONFLICT", "You already have a review for this movie.", 409)

    data = request.get_json() or {}
    body = data.get("body", "").strip()
    contains_spoiler = bool(data.get("contains_spoiler", False))

    if not body:
        return api_error("VALIDATION_ERROR", "Review cannot be empty.", 400, fields={"body": "Required"})

    new_review = Review(
        rating_id=rating.id,
        body=body,
        contains_spoiler=contains_spoiler,
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify(review_to_dict(new_review)), 201


@bp.route("/reviews/<int:review_id>", methods=["PUT", "PATCH"])
def update_review(review_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    review = db.session.get(Review, review_id)
    if not review:
        return api_error("NOT_FOUND", "Review not found.", 404)

    if review.rating.user_id != user_id:
        return api_error("FORBIDDEN", "You can only edit your own review.", 403)

    data = request.get_json() or {}

    if "body" in data:
        body = data.get("body", "").strip()
        if not body:
            return api_error("VALIDATION_ERROR", "Review cannot be empty.", 400, fields={"body": "Cannot be blank"})
        review.body = body

    if "contains_spoiler" in data:
        review.contains_spoiler = bool(data.get("contains_spoiler"))

    db.session.commit()
    return jsonify(review_to_dict(review)), 200


@bp.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    review = db.session.get(Review, review_id)
    if not review:
        return api_error("NOT_FOUND", "Review not found.", 404)

    if review.rating.user_id != user_id:
        return api_error("FORBIDDEN", "You can only delete your own review.", 403)

    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted."}), 200