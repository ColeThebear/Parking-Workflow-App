"""
Edge-case and negative-path tests for the /auth router.
Happy-path login is covered in test_auth.py.
"""


def test_register_success(client):
    resp = client.post("/v1/auth/register", json={
        "email": "newuser_reg@test.com",
        "password": "StrongPass1!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "PARKER"
    assert "access_token" not in data   # token lives in HttpOnly cookie


def test_register_duplicate_email(client):
    payload = {"email": "dup_reg@test.com", "password": "StrongPass1!"}
    client.post("/v1/auth/register", json=payload)
    resp = client.post("/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_register_weak_password_rejected(client):
    resp = client.post("/v1/auth/register", json={
        "email": "weakpass_reg@test.com",
        "password": "abc",
    })
    assert resp.status_code == 400


def test_login_wrong_password(client, make_user):
    make_user("wrongpw@test.com")
    resp = client.post("/v1/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "NotTheRightOne!",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/v1/auth/login", json={
        "email": "ghost@test.com",
        "password": "Test123!",
    })
    assert resp.status_code == 401


def test_missing_token_returns_401(client):
    resp = client.get("/v1/student/active")
    assert resp.status_code == 401


def test_invalid_token_returns_401(client):
    resp = client.get(
        "/v1/student/active",
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    assert resp.status_code == 401


def test_refresh_token_flow(client, make_user):
    make_user("refresh_flow@test.com")
    # Login sets the refresh_token HttpOnly cookie on the TestClient's cookie jar
    login = client.post("/v1/auth/login", json={
        "email": "refresh_flow@test.com",
        "password": "Test123!",
    })
    assert login.status_code == 200

    # TestClient sends the cookie automatically — no body needed
    resp = client.post("/v1/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["role"] == "PARKER"

    # New access_token cookie should allow protected routes
    protected = client.get("/v1/student/active")
    assert protected.status_code in (200, 404)  # 404 = no session, but auth passed


def test_refresh_with_invalid_token(client):
    resp = client.post("/v1/auth/refresh", json={"refresh_token": "bad.token.here"})
    assert resp.status_code == 401


def test_change_password(client, make_user, auth_headers):
    make_user("changepw@test.com", password="OldPass1!")
    headers = auth_headers("changepw@test.com", "OldPass1!")

    resp = client.post(
        "/v1/auth/change-password",
        headers=headers,
        json={"current_password": "OldPass1!", "new_password": "NewPass2!"},
    )
    assert resp.status_code == 200

    # Old password no longer works
    assert client.post("/v1/auth/login", json={
        "email": "changepw@test.com", "password": "OldPass1!",
    }).status_code == 401

    # New password works
    assert client.post("/v1/auth/login", json={
        "email": "changepw@test.com", "password": "NewPass2!",
    }).status_code == 200


def test_change_password_wrong_current(client, make_user, auth_headers):
    make_user("changepw_bad@test.com")
    headers = auth_headers("changepw_bad@test.com")

    resp = client.post(
        "/v1/auth/change-password",
        headers=headers,
        json={"current_password": "WrongCurrent!", "new_password": "NewPass2!"},
    )
    assert resp.status_code == 400


def test_wrong_role_returns_403(client, make_user, auth_headers):
    make_user("parker_403@test.com", role="PARKER")
    headers = auth_headers("parker_403@test.com")

    resp = client.get("/v1/enforcement/lookup?plate=XYZ999", headers=headers)
    assert resp.status_code == 403
