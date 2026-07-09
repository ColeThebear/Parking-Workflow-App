"""CSRF middleware: double-submit cookie validation."""


def test_csrf_cookie_set_on_login_response(client, make_user):
    """The CSRF cookie must be present on the login response for new sessions."""
    make_user("csrf_cookie@test.com")
    resp = client.post("/v1/auth/login", json={
        "email": "csrf_cookie@test.com",
        "password": "Test123!",
    })
    assert resp.status_code == 200
    assert "csrf_token" in resp.cookies


def test_csrf_blocks_cookie_auth_without_header(client, make_user):
    """A cookie-authenticated POST with no X-CSRF-Token header must return 403."""
    make_user("csrf_block@test.com")
    # Login populates the cookie jar (login itself is CSRF-exempt)
    client.post("/v1/auth/login", json={
        "email": "csrf_block@test.com",
        "password": "Test123!",
    })
    # POST using cookies only, no CSRF header — must be blocked
    resp = client.post("/v1/student/start", json={"plate": "BLK001", "zone": "A1"})
    assert resp.status_code == 403
    assert "CSRF" in resp.json()["detail"]


def test_csrf_passes_with_matching_token(client, make_user):
    """A cookie-authenticated POST with a matching X-CSRF-Token header must succeed."""
    make_user("csrf_pass@test.com")
    client.post("/v1/auth/login", json={
        "email": "csrf_pass@test.com",
        "password": "Test123!",
    })
    token = client.cookies.get("csrf_token")
    assert token, "CSRF cookie must be set after login"

    resp = client.post(
        "/v1/student/start",
        json={"plate": "PSS001", "zone": "A1"},
        headers={"X-CSRF-Token": token},
    )
    assert resp.status_code == 200


def test_csrf_blocks_mismatched_token(client, make_user):
    """A tampered CSRF header value must be rejected."""
    make_user("csrf_mismatch@test.com")
    client.post("/v1/auth/login", json={
        "email": "csrf_mismatch@test.com",
        "password": "Test123!",
    })
    resp = client.post(
        "/v1/student/start",
        json={"plate": "MIS001", "zone": "A1"},
        headers={"X-CSRF-Token": "wrong-token-value"},
    )
    assert resp.status_code == 403


def test_csrf_skipped_for_bearer_auth(client, make_user, auth_headers):
    """Bearer-token requests must bypass CSRF entirely (API / test clients)."""
    make_user("csrf_bearer@test.com")
    headers = auth_headers("csrf_bearer@test.com")
    # No CSRF header, but Bearer token present — must succeed
    resp = client.post(
        "/v1/student/start",
        json={"plate": "BRR001", "zone": "A1"},
        headers=headers,
    )
    assert resp.status_code == 200


def test_csrf_token_endpoint_sets_cookie(client):
    """/auth/csrf-token must issue (or renew) the CSRF cookie."""
    resp = client.get("/v1/auth/csrf-token")
    assert resp.status_code == 200
    assert "csrf_token" in resp.json()
    assert "csrf_token" in resp.cookies
