"""Watchlist. Owner: Dev 5 (DATA-04)."""
from flask import Blueprint, jsonify, request, session
from app.api_errors import api_error
from app.extensions import db
from app.models.watchlist import WATCHLIST_STATUSES, WatchlistItem
from app.services.tmdb import get_or_fetch_movie

bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


def watchlist_to_dict(item):
    return {
        "tmdb_id": item.tmdb_id,
        "title": item.movie.title if item.movie else None,
        "poster_path": item.movie.poster_path if item.movie else None,
        "status": item.status,
        "added_at": item.added_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


@bp.route("", methods=["GET"])
def get_watchlist():
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    status = request.args.get("status")
    if status and status not in WATCHLIST_STATUSES:
        return api_error(
            "VALIDATION_ERROR",
            "Invalid watchlist status.",
            400,
            fields={"status": f"Must be one of: {', '.join(WATCHLIST_STATUSES)}"},
        )

    all_items = (
        WatchlistItem.query.filter_by(user_id=user_id)
        .order_by(WatchlistItem.added_at.desc())
        .all()
    )

    counts = {
        "plan": 0,
        "watched": 0,
        "on_hold": 0,
        "dropped": 0,
    }
    items = []

    for item in all_items:
        if item.status in counts:
            counts[item.status] += 1
        if not status or item.status == status:
            items.append(watchlist_to_dict(item))

    return jsonify({"items": items, "counts": counts}), 200


@bp.route("/<int:tmdb_id>", methods=["PUT"])
def upsert_watchlist_item(tmdb_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    data = request.get_json() or {}
    status = data.get("status", "plan")

    if status not in WATCHLIST_STATUSES:
        return api_error(
            "VALIDATION_ERROR",
            "Invalid watchlist status.",
            400,
            fields={"status": f"Must be one of: {', '.join(WATCHLIST_STATUSES)}"},
        )

    item = WatchlistItem.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()

    if item:
        item.status = status
        db.session.commit()
        return jsonify(watchlist_to_dict(item)), 200

    movie = get_or_fetch_movie(tmdb_id)
    if not movie:
        return api_error("NOT_FOUND", "Movie not found.", 404)

    new_item = WatchlistItem(
        user_id=user_id,
        tmdb_id=movie.tmdb_id,
        status=status,
    )
    db.session.add(new_item)
    db.session.commit()

    return jsonify(watchlist_to_dict(new_item)), 201


@bp.route("/<int:tmdb_id>", methods=["DELETE"])
def remove_from_watchlist(tmdb_id):
    user_id = session.get("user_id")
    if not user_id:
        return api_error("UNAUTHORIZED", "Please log in first.", 401)

    item = WatchlistItem.query.filter_by(user_id=user_id, tmdb_id=tmdb_id).first()
    if not item:
        return api_error("NOT_FOUND", "Movie not found in your watchlist.", 404)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Removed from watchlist."}), 200