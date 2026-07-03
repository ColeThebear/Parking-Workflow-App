"""
Edge-case and negative-path tests for the /auth router.
Happy-path login is covered in test_auth.py.
"""


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "email": "newuser_reg@test.com",
        "password": "StrongPass1!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "PARKER"


def test_register_duplicate_email(client):
    payload = {"email": "dup_reg@test.com", "password": "StrongPass1!"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_weak_password_rejected(client):
    resp = client.post("/auth/register", json={
        "email": "weakpass_reg@test.com",
        "password": "abc",
    })
    assert resp.status_code == 400


def test_login_wrong_password(client, make_user):
    make_user("wrongpw@test.com")
    resp = client.post("/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "NotTheRightOne!",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={
        "email": "ghost@test.com",
        "password": "Test123!",
    })
    assert resp.status_code == 401


def test_missing_token_returns_401(client):
    resp = client.get("/student/active")
    assert resp.status_code == 401


def test_invalid_token_returns_401(client):
    resp = client.get(
        "/student/active",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert resp.status_code == 401


def test_refresh_token_flow(client, make_user):
    make_user("refresh_flow@test.com")
    login = client.post("/auth/login", json={
        "email": "refresh_flow@test.com",
        "password": "Test123!",
    })
    assert login.status_code == 200
    refresh_token = login.json().get("refresh_token")
    assert refresh_token, "Login response must include refresh_token"

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    # Verify the new token actually works on a protected route
    protected = client.get(
        "/student/active",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert protected.status_code in (200, 404)  # 404 = no session, but auth succeeded


def test_refresh_with_invalid_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


def test_change_password(client, make_user):
    make_user("changepw@test.com", password="OldPass1!")
    login = client.post("/auth/login", json={
        "email": "changepw@test.com",
        "password": "OldPass1!",
    })
    token = login.json()["access_token"]

    resp = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "OldPass1!", "new_password": "NewPass2!"},
    )
    assert resp.status_code == 200

    # Old password no longer works
    assert client.post("/auth/login", json={
        "email": "changepw@test.com", "password": "OldPass1!",
    }).status_code == 401

    # New password works
    assert client.post("/auth/login", json={
        "email": "changepw@test.com", "password": "NewPass2!",
    }).status_code == 200


def test_change_password_wrong_current(client, make_user):
    make_user("changepw_bad@test.com")
    login = client.post("/auth/login", json={
        "email": "changepw_bad@test.com", "password": "Test123!",
    })
    token = login.json()["access_token"]

    resp = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "WrongCurrent!", "new_password": "NewPass2!"},
    )
    assert resp.status_code == 400


def test_wrong_role_returns_403(client, make_user):
    make_user("parker_403@test.com", role="PARKER")
    login = client.post("/auth/login", json={
        "email": "parker_403@test.com", "password": "Test123!",
    })
    token = login.json()["access_token"]

    resp = client.get(
        "/enforcement/lookup?plate=XYZ999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
