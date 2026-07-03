"""Full parking session lifecycle and edge cases."""
from datetime import datetime, timezone, timedelta

from app.models.parking import ParkingSession


def test_start_session(client, make_user, auth_headers):
    make_user("park_start@test.com")
    headers = auth_headers("park_start@test.com")

    resp = client.post("/student/start", headers=headers,
                       json={"plate": "PKS001", "zone": "A1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["plate"] == "PKS001"
    assert data["zone"] == "A1"
    assert data["expires_at"] is not None


def test_duplicate_active_session_rejected(client, make_user, auth_headers):
    make_user("park_dup@test.com")
    headers = auth_headers("park_dup@test.com")

    client.post("/student/start", headers=headers, json={"plate": "PKD001", "zone": "B2"})
    resp = client.post("/student/start", headers=headers, json={"plate": "PKD002", "zone": "C3"})
    assert resp.status_code == 400
    assert "active" in resp.json()["detail"].lower()


def test_get_active_session(client, make_user, auth_headers):
    make_user("park_active@test.com")
    headers = auth_headers("park_active@test.com")

    client.post("/student/start", headers=headers, json={"plate": "PKA001", "zone": "D4"})
    resp = client.get("/student/active", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["plate"] == "PKA001"


def test_get_active_session_when_none(client, make_user, auth_headers):
    make_user("park_none@test.com")
    headers = auth_headers("park_none@test.com")

    resp = client.get("/student/active", headers=headers)
    assert resp.status_code == 404


def test_end_session(client, make_user, auth_headers):
    make_user("park_end@test.com")
    headers = auth_headers("park_end@test.com")

    client.post("/student/start", headers=headers, json={"plate": "PKE001", "zone": "E5"})
    resp = client.post("/student/end", headers=headers)
    assert resp.status_code == 200

    # Active session should now be gone
    resp2 = client.get("/student/active", headers=headers)
    assert resp2.status_code == 404


def test_session_history(client, make_user, auth_headers):
    make_user("park_hist@test.com")
    headers = auth_headers("park_hist@test.com")

    client.post("/student/start", headers=headers, json={"plate": "PKH001", "zone": "F6"})
    client.post("/student/end", headers=headers)

    resp = client.get("/student/my-sessions", headers=headers)
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1
    assert any(s["plate"] == "PKH001" for s in sessions)


def test_unauthenticated_start_rejected(client):
    resp = client.post("/student/start", json={"plate": "NOAUTH", "zone": "Z9"})
    assert resp.status_code == 401


def test_plate_normalised_to_uppercase(client, make_user, auth_headers):
    make_user("park_upper@test.com")
    headers = auth_headers("park_upper@test.com")

    resp = client.post("/student/start", headers=headers,
                       json={"plate": "abc123", "zone": "A1"})
    assert resp.status_code == 200
    assert resp.json()["plate"] == "ABC123"


def test_expired_session_not_returned_as_active(client, make_user, auth_headers, db):
    make_user("park_exp@test.com")
    headers = auth_headers("park_exp@test.com")

    # Start a session then manually expire it in the DB
    start = client.post("/student/start", headers=headers,
                        json={"plate": "PKEXP1", "zone": "G7"})
    session_id = start.json()["session_id"]

    session = db.query(ParkingSession).filter(ParkingSession.id == session_id).first()
    session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    resp = client.get("/student/active", headers=headers)
    assert resp.status_code == 404
