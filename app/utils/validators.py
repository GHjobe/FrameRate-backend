import re
from typing import Any, cast

from .errors import ValidationError
from .security import check_password_policy

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RATING_STEP = 1  # change to 0.5 if the team picks half stars
MAX_REVIEW_LENGTH = 5000


def _body(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        return cast(dict[str, Any], data)
    return {}


def _str_list(value: Any) -> list[str] | None:
    """Returns the value as list[str], or None if it isn't a list of strings."""
    if not isinstance(value, list):
        return None
    items = cast(list[Any], value)
    if not all(isinstance(item, str) for item in items):
        return None
    return cast(list[str], items)


def validate_register(data: Any) -> dict[str, str]:
    body = _body(data)
    errors: dict[str, str] = {}
    email = str(body.get("email", "")).strip().lower()
    username = str(body.get("username", "")).strip()
    raw_password = body.get("password")
    password = raw_password if isinstance(raw_password, str) else ""

    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    if not (3 <= len(username) <= 30):
        errors["username"] = "Username must be 3 to 30 characters."
    if not password:
        errors["password"] = "Password is required."
    else:
        problems = check_password_policy(password)
        if problems:
            errors["password"] = " ".join(problems)

    if errors:
        raise ValidationError(errors)
    return {"email": email, "username": username, "password": password}


def validate_login(data: Any) -> dict[str, str]:
    body = _body(data)
    errors: dict[str, str] = {}
    email = str(body.get("email", "")).strip().lower()
    raw_password = body.get("password")
    password = raw_password if isinstance(raw_password, str) else ""

    if not email:
        errors["email"] = "Email is required."
    if not password:
        errors["password"] = "Password is required."
    if errors:
        raise ValidationError(errors)
    return {"email": email, "password": password}


def validate_rating(data: Any) -> dict[str, Any]:
    body = _body(data)
    raw = body.get("rating", body.get("value"))
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        raise ValidationError({"rating": "Rating must be a number."})
    try:
        number = float(raw)
    except ValueError:
        raise ValidationError({"rating": "Rating must be a number."}) from None
    if not (1 <= number <= 5) or (number / RATING_STEP) % 1 != 0:
        step = "whole stars" if RATING_STEP == 1 else "half stars"
        raise ValidationError({"rating": f"Rating must be 1 to 5 in {step}."})
    return {"rating": int(number) if RATING_STEP == 1 else number}


def validate_review(data: Any) -> dict[str, Any]:
    payload = _body(data)
    errors: dict[str, str] = {}
    text = str(payload.get("body", payload.get("text", ""))).strip()
    if not text:
        errors["body"] = "Review cannot be empty."
    elif len(text) > MAX_REVIEW_LENGTH:
        errors["body"] = f"Review must be under {MAX_REVIEW_LENGTH} characters."
    if "containsSpoilers" in payload and not isinstance(payload["containsSpoilers"], bool):
        errors["containsSpoilers"] = "Must be true or false."
    if errors:
        raise ValidationError(errors)
    return {
        "body": text,
        "contains_spoilers": bool(payload.get("containsSpoilers", False)),
    }


def validate_preferences(data: Any, options: dict[str, set[str]]) -> dict[str, Any]:
    """options = valid ids per list: genres_ids, services_ids, regions_ids, languages_ids."""
    body = _body(data)
    errors: dict[str, str] = {}

    genres = _str_list(body.get("genres", []))
    services = _str_list(body.get("services", []))
    region = body.get("region")
    language = body.get("language")
    blur = body.get("blurSpoilers", False)

    if genres is None or any(g not in options["genres_ids"] for g in genres):
        errors["genres"] = "Contains an invalid genre."
    if services is None or any(s not in options["services_ids"] for s in services):
        errors["services"] = "Contains an invalid streaming service."
    if region not in options["regions_ids"]:
        errors["region"] = "Choose a valid region."
    if language not in options["languages_ids"]:
        errors["language"] = "Choose a valid language."
    if not isinstance(blur, bool):
        errors["blurSpoilers"] = "Must be true or false."

    if errors:
        raise ValidationError(errors)
    return {
        "genres": genres,
        "services": services,
        "region": region,
        "language": language,
        "blurSpoilers": blur,
    }