import pytest

from app.extensions import db
from app.models import User

GOOD = {"username": "demo_user", "email": "Demo@Example.com", "password": "Passw0rd123"}


def register(client, **overrides):
    return client.post("/api/auth/register", json={**GOOD, **overrides})


def test_register_creates_the_user_and_signs_them_in(client):
    response = register(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body == {
        "id": body["id"],
        "username": "demo_user",
        "email": "demo@example.com",  # stored in lowercase
        "role": "user",
        "emailVerified": False,
        "onboardingCompleted": False,
    }
    assert "password" not in response.get_data(as_text=True).lower()
    assert db.session.query(User).one().password_hash != GOOD["password"]

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json() == body


@pytest.mark.parametrize(
    "field,value",
    [
        ("username", "ab"),
        ("username", "has space"),
        ("username", "x" * 21),
        ("email", "not-an-email"),
        ("password", "short1"),
        ("password", "onlyletters"),
        ("password", "12345678"),
    ],
)
def test_register_rejects_bad_input(client, field, value):
    response = register(client, **{field: value})
    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION"
    assert field in error["fields"]
    assert db.session.query(User).count() == 0


def test_duplicate_username_or_email_is_a_conflict_ignoring_case(client):
    assert register(client).status_code == 201

    response = register(client, username="DEMO_USER", email="other@example.com")
    assert response.status_code == 409
    assert "username" in response.get_json()["error"]["fields"]

    response = register(client, username="someone_else", email="DEMO@EXAMPLE.COM")
    assert response.status_code == 409
    assert "email" in response.get_json()["error"]["fields"]


def test_login_works_with_email_or_username(client):
    register(client)
    client.post("/api/auth/logout")
    for identifier in ("demo@example.com", "DEMO_USER"):
        response = client.post("/api/auth/login", json={"email": identifier, "password": GOOD["password"]})
        assert response.status_code == 200
        assert response.get_json()["username"] == "demo_user"
        client.post("/api/auth/logout")


def test_wrong_password_and_unknown_user_look_the_same(client):
    register(client)
    client.post("/api/auth/logout")
    wrong = client.post("/api/auth/login", json={"email": "demo@example.com", "password": "Wrong1234"})
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "Wrong1234"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()
    assert wrong.get_json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert client.get("/api/auth/me").status_code == 401


def test_login_needs_both_fields(client):
    response = client.post("/api/auth/login", json={"email": "demo@example.com"})
    assert response.status_code == 400
    assert "password" in response.get_json()["error"]["fields"]


def test_logout_ends_the_session(client):
    register(client)
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/logout").status_code == 204  # fine when already logged out


def test_me_needs_a_login(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHENTICATED"


def test_body_must_be_json(client):
    assert client.post("/api/auth/register", data="nope").status_code == 400


def test_session_cookie_is_httponly_and_samesite(client):
    cookie = register(client).headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie