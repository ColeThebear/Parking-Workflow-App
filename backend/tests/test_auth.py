from app.models.user import User
from app.utils.security import get_password_hash


def test_login_success(client, db):
    user = User(
        email="testuser@test.com",
        password_hash=get_password_hash("testpass"),
        role="PARKER"
    )
    db.add(user)
    db.commit()

    response = client.post("/v1/auth/login", json={
        "email": "testuser@test.com",
        "password": "testpass"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "PARKER"
    # Tokens are in HttpOnly cookies, not the response body
    assert "access_token" not in data


def test_seeded_account_login(client):
    response = client.post("/v1/auth/login", json={
        "email": "jsmith@suny.edu",
        "password": "Test123!",
    })
    assert response.status_code == 200
    assert response.json().get("role") == "PARKER"


def test_login_sets_httponly_cookies(client, db):
    db.add(User(
        email="cookie_check@test.com",
        password_hash=get_password_hash("Test123!"),
        role="PARKER",
    ))
    db.commit()
    response = client.post("/v1/auth/login", json={
        "email": "cookie_check@test.com",
        "password": "Test123!",
    })
    assert response.status_code == 200
    assert "access_token" in response.cookies


def test_login_failure(client):
    response = client.post("/v1/auth/login", json={
        "email": "nobody@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401