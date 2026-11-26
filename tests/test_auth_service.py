import pytest

from app.extensions import db
from app.models import User
from app.services.auth_service import (
    DuplicateUserError,
    authenticate,
    create_user,
    find_taken_fields,
    get_user,
)


def test_create_user_hashes_the_password(app):
    user = create_user("demo", "demo@example.com", "Passw0rd123")
    assert user.id is not None
    assert user.password_hash != "Passw0rd123"


def test_create_user_raises_on_a_duplicate_ignoring_case(app):
    create_user("demo", "demo@example.com", "Passw0rd123")
    with pytest.raises(DuplicateUserError):
        create_user("DEMO", "other@example.com", "Passw0rd123")
    assert db.session.query(User).count() == 1


def test_find_taken_fields_ignores_case(app):
    create_user("demo", "demo@example.com", "Passw0rd123")
    assert set(find_taken_fields("DEMO", "other@example.com")) == {"username"}
    assert set(find_taken_fields("someone", "DEMO@example.com")) == {"email"}
    assert find_taken_fields("someone", "other@example.com") == {}


def test_authenticate_by_email_or_username(app):
    user = create_user("demo", "demo@example.com", "Passw0rd123")
    assert authenticate("demo@example.com", "Passw0rd123") == user
    assert authenticate("DEMO", "Passw0rd123") == user
    assert authenticate("demo", "WrongPass1") is None
    assert authenticate("nobody", "Passw0rd123") is None


def test_get_user(app):
    user = create_user("demo", "demo@example.com", "Passw0rd123")
    assert get_user(user.id) == user
    assert get_user(None) is None
    assert get_user(9999) is None