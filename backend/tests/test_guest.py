"""Guest registration and login flow."""


def test_guest_register(client):
    resp = client.post("/v1/auth/guest-register", json={
        "email": "guest_new@test.com",
        "name": "Guest User",
        "password": "GuestPass1!",
        "license_plate": "GST001",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "GUEST"
    assert "access_token" not in data  # token lives in HttpOnly cookie


def test_guest_login_after_register(client):
    client.post("/v1/auth/guest-register", json={
        "email": "guest_login@test.com",
        "name": "Guest Login",
        "password": "GuestPass1!",
        "license_plate": "GST002",
    })
    resp = client.post("/v1/auth/login", json={
        "email": "guest_login@test.com",
        "password": "GuestPass1!",
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "GUEST"


def test_guest_duplicate_email_rejected(client):
    payload = {
        "email": "guest_dup@test.com",
        "name": "Dup Guest",
        "password": "GuestPass1!",
        "license_plate": "GST003",
    }
    client.post("/v1/auth/guest-register", json=payload)
    resp = client.post("/v1/auth/guest-register", json=payload)
    assert resp.status_code == 400


def test_guest_register_without_plate(client):
    resp = client.post("/v1/auth/guest-register", json={
        "email": "guest_noplate@test.com",
        "name": "No Plate Guest",
        "password": "GuestPass1!",
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "GUEST"
