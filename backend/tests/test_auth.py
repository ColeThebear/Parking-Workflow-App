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

    response = client.post("/auth/login", json={
        "email": "testuser@test.com",
        "password": "testpass"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_seeded_account_login(client):
    # when the API starts it seeds several known users, make sure one of them
    # can authenticate using the documented credentials.
    response = client.post("/auth/login", json={
        "email": "jsmith@suny.edu",
        "password": "Test123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token")


def test_login_failure(client):
    response = client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401