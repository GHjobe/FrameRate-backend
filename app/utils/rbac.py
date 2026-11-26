# role-based access control

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import g, session

from .errors import ApiError

F = TypeVar("F", bound=Callable[..., Any])

ROLE_LEVELS: dict[str, int] = {"user": 1, "moderator": 2, "admin": 3}


def _load_user() -> Any:
    # Imported here to avoid circular imports. Adjust to Dev 3's paths.
    from app.extensions import db
    from app.models import User

    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def _require_user() -> Any:
    """Loads the logged-in user into g.current_user or raises a 401."""
    user = _load_user()
    if user is None:
        session.pop("user_id", None)
        raise ApiError("You must be logged in.", status=401, code="UNAUTHORIZED")
    g.current_user = user
    return user


def login_required(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _require_user()
        return fn(*args, **kwargs)

    return cast(F, wrapper)


def role_required(role: str) -> Callable[[F], F]:
    if role not in ROLE_LEVELS:
        raise ValueError(f"Unknown role: {role}")

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = _require_user()
            user_level = ROLE_LEVELS.get(str(user.role), 0)
            if user_level < ROLE_LEVELS[role]:
                raise ApiError(
                    "You don't have permission to do that.",
                    status=403,
                    code="FORBIDDEN",
                )
            return fn(*args, **kwargs)

        return cast(F, wrapper)

    return decorator