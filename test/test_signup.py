# tests/test_signup.py
import pytest

from application.container import set_container
from database.db_model import db as _db
from app import create_app
from config import config


@pytest.fixture(scope="function")
def app(monkeypatch):
    # Point the app at an in-memory DB for tests
    monkeypatch.setattr(config.database, "url", "sqlite:///:memory:")
    # Reset DI container so it rebuilds against this app/db
    set_container(None)

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,  # avoid CSRF on test POSTs
        SERVER_NAME="localhost",
    )
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_signup_get_renders_form(client):
    res = client.get("/signup")
    assert res.status_code == 200
    # Spot-check the page looks like the sign-up screen
    assert b"Sign Up" in res.data or b"username" in res.data.lower()


def test_signup_success_json(client):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "s3cret!",
        # Optional fields are fine to omit
    }
    res = client.post("/signup", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "Signup successful" in data["message"]


def test_signup_missing_field_returns_error(client):
    # Missing password → controller should complain
    payload = {"username": "bob", "email": "bob@example.com"}
    res = client.post("/signup", json=payload)
    assert res.status_code == 200  # controller returns JSON, not 4xx
    data = res.get_json()
    assert data["success"] is False
    assert data["message"] == "Password is required."


def test_signup_duplicate_email_and_username(client):
    first = {"username": "charlie", "email": "charlie@example.com", "password": "pw1"}
    res1 = client.post("/signup", json=first)
    assert res1.get_json()["success"] is True

    # Duplicate email
    dup_email = {"username": "charlie2", "email": "charlie@example.com", "password": "pw2"}
    res2 = client.post("/signup", json=dup_email)
    data2 = res2.get_json()
    assert data2["success"] is False
    assert "already exists" in data2["message"]

    # Duplicate username
    dup_user = {"username": "charlie", "email": "charlie2@example.com", "password": "pw3"}
    res3 = client.post("/signup", json=dup_user)
    data3 = res3.get_json()
    assert data3["success"] is False
    assert "Username already taken" in data3["message"]
