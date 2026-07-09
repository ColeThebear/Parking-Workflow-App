"""Admin router: stats, users, citations, balance credit, password reset."""
from app.models.token import TokenBalance


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_balance(db, user_id: int) -> TokenBalance:
    """Create a TokenBalance row if one doesn't already exist."""
    bal = db.query(TokenBalance).filter(TokenBalance.user_id == user_id).first()
    if not bal:
        bal = TokenBalance(user_id=user_id, balance=0)
        db.add(bal)
        db.commit()
        db.refresh(bal)
    return bal


# ── Stats ─────────────────────────────────────────────────────────────────────

def test_admin_stats(client, make_user, auth_headers):
    make_user("admin_stats@test.com", role="ADMIN", admin_permission="full_admin")
    headers = auth_headers("admin_stats@test.com")

    resp = client.get("/v1/admin/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for key in ("active_sessions", "total_users", "total_students",
                "total_officers", "total_citations", "unpaid_citations"):
        assert key in data


def test_non_admin_blocked_from_stats(client, make_user, auth_headers):
    make_user("nonadmin_stats@test.com", role="PARKER")
    headers = auth_headers("nonadmin_stats@test.com")

    resp = client.get("/v1/admin/stats", headers=headers)
    assert resp.status_code == 403


# ── Users ─────────────────────────────────────────────────────────────────────

def test_admin_list_users(client, make_user, auth_headers):
    make_user("admin_users@test.com", role="ADMIN", admin_permission="full_admin")
    headers = auth_headers("admin_users@test.com")

    resp = client.get("/v1/admin/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert len(users) > 0
    assert all("email" in u and "role" in u for u in users)


# ── Citations ─────────────────────────────────────────────────────────────────

def test_admin_list_all_citations(client, make_user, auth_headers):
    make_user("admin_cite_list@test.com", role="ADMIN", admin_permission="full_admin")
    make_user("enf_for_admin@test.com", role="ENFORCEMENT")
    admin_headers = auth_headers("admin_cite_list@test.com")
    enf_headers = auth_headers("enf_for_admin@test.com")

    client.post("/v1/enforcement/citations", headers=enf_headers, json={
        "vehicle_plate": "ADM001", "zone": "A1", "violation_type": "No Valid Session",
    })

    resp = client.get("/v1/admin/citations", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    plates = [c["plate"] for c in resp.json()]
    assert "ADM001" in plates


def test_admin_mark_citation_paid(client, make_user, auth_headers):
    make_user("admin_mark_paid@test.com", role="ADMIN", admin_permission="full_admin")
    make_user("enf_mark_paid@test.com", role="ENFORCEMENT")
    admin_headers = auth_headers("admin_mark_paid@test.com")
    enf_headers = auth_headers("enf_mark_paid@test.com")

    cite_resp = client.post("/v1/enforcement/citations", headers=enf_headers, json={
        "vehicle_plate": "PAD001", "zone": "B2", "violation_type": "Expired Session",
    })
    citation_id = cite_resp.json()["id"]

    resp = client.patch(f"/v1/admin/citations/{citation_id}/paid", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify in the admin citation list
    list_resp = client.get("/v1/admin/citations", headers=admin_headers)
    cite = next(c for c in list_resp.json() if c["id"] == citation_id)
    assert cite["paid"] is True


def test_admin_mark_nonexistent_citation_paid(client, make_user, auth_headers):
    make_user("admin_cite_404@test.com", role="ADMIN", admin_permission="full_admin")
    headers = auth_headers("admin_cite_404@test.com")

    resp = client.patch("/v1/admin/citations/999999/paid", headers=headers)
    assert resp.status_code == 404


# ── Balance credit ────────────────────────────────────────────────────────────

def test_admin_credit_balance(client, make_user, auth_headers, db):
    admin = make_user("admin_credit@test.com", role="ADMIN", admin_permission="full_admin")
    student = make_user("student_credit@test.com", role="PARKER")
    _ensure_balance(db, student.id)

    admin_headers = auth_headers("admin_credit@test.com")

    resp = client.post("/v1/admin/balance/credit", headers=admin_headers, json={
        "user_id": student.id,
        "amount": 1000,
        "description": "Test credit",
    })
    assert resp.status_code == 200
    assert resp.json()["balance"] == 1000


def test_admin_credit_no_balance_account(client, make_user, auth_headers):
    make_user("admin_credit_nobal@test.com", role="ADMIN", admin_permission="full_admin")
    admin_headers = auth_headers("admin_credit_nobal@test.com")

    resp = client.post("/v1/admin/balance/credit", headers=admin_headers, json={
        "user_id": 999999,
        "amount": 500,
        "description": "Ghost user",
    })
    assert resp.status_code == 404


# ── Password reset ────────────────────────────────────────────────────────────

def test_admin_reset_password(client, make_user, auth_headers):
    make_user("admin_resetpw@test.com", role="ADMIN", admin_permission="full_admin")
    target = make_user("target_resetpw@test.com")
    admin_headers = auth_headers("admin_resetpw@test.com")

    resp = client.post("/v1/admin/reset-password", headers=admin_headers, json={
        "user_id": target.id,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == target.id
    assert "temp_password" in data
    assert len(data["temp_password"]) >= 12

    # The temp password must actually work for login
    login = client.post("/v1/auth/login", json={
        "email": "target_resetpw@test.com",
        "password": data["temp_password"],
    })
    assert login.status_code == 200


def test_admin_reset_password_unknown_user(client, make_user, auth_headers):
    make_user("admin_resetpw_404@test.com", role="ADMIN", admin_permission="full_admin")
    headers = auth_headers("admin_resetpw_404@test.com")

    resp = client.post("/v1/admin/reset-password", headers=headers, json={"user_id": 999999})
    assert resp.status_code == 404
