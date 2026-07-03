"""Token balance: creation on first access, admin credit, transaction history."""
from app.models.token import TokenBalance


def test_balance_created_on_first_access(client, make_user, auth_headers, db):
    student = make_user("bal_first@test.com")
    headers = auth_headers("bal_first@test.com")

    # No balance row exists yet
    assert db.query(TokenBalance).filter(TokenBalance.user_id == student.id).first() is None

    resp = client.get("/student/balance", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 0
    assert isinstance(data["transactions"], list)

    # Row should now exist
    assert db.query(TokenBalance).filter(TokenBalance.user_id == student.id).first() is not None


def test_balance_starts_at_zero(client, make_user, auth_headers):
    make_user("bal_zero@test.com")
    headers = auth_headers("bal_zero@test.com")

    resp = client.get("/student/balance", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0


def test_balance_reflects_admin_credit(client, make_user, auth_headers, db):
    admin = make_user("bal_admin@test.com", role="ADMIN", admin_permission="full_admin")
    student = make_user("bal_student@test.com")
    admin_headers = auth_headers("bal_admin@test.com")
    student_headers = auth_headers("bal_student@test.com")

    # Initialise balance by accessing it
    client.get("/student/balance", headers=student_headers)

    client.post("/admin/balance/credit", headers=admin_headers, json={
        "user_id": student.id,
        "amount": 2500,
        "description": "Test top-up",
    })

    resp = client.get("/student/balance", headers=student_headers)
    assert resp.status_code == 200
    assert resp.json()["balance"] == 2500


def test_transaction_history_includes_credit(client, make_user, auth_headers, db):
    admin = make_user("bal_txn_admin@test.com", role="ADMIN", admin_permission="full_admin")
    student = make_user("bal_txn_student@test.com")
    admin_headers = auth_headers("bal_txn_admin@test.com")
    student_headers = auth_headers("bal_txn_student@test.com")

    client.get("/student/balance", headers=student_headers)  # init
    client.post("/admin/balance/credit", headers=admin_headers, json={
        "user_id": student.id, "amount": 750, "description": "Gift",
    })

    resp = client.get("/student/balance", headers=student_headers)
    txns = resp.json()["transactions"]
    assert len(txns) >= 1
    assert any(t["amount"] == 750 and t["tx_type"] == "ADMIN" for t in txns)


def test_balance_requires_auth(client):
    resp = client.get("/student/balance")
    assert resp.status_code == 401
