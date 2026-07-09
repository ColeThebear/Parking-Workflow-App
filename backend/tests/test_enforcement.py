"""Enforcement router: plate lookup, citations, role guards."""
from datetime import datetime, timezone, timedelta

from app.models.parking import ParkingSession


def _active_session(db, user_id: int, plate: str, zone: str = "A1") -> ParkingSession:
    now = datetime.now(timezone.utc)
    s = ParkingSession(
        user_id=user_id,
        vehicle_plate=plate,
        zone=zone,
        active=True,
        started_at=now,
        expires_at=now + timedelta(hours=1),
    )
    db.add(s)
    db.commit()
    return s


# ── Plate lookup ──────────────────────────────────────────────────────────────

def test_lookup_plate_found(client, make_user, auth_headers, db):
    parker = make_user("enf_parker_found@test.com")
    enforcer = make_user("enf_officer_found@test.com", role="ENFORCEMENT")
    _active_session(db, parker.id, "ENF100")
    headers = auth_headers("enf_officer_found@test.com")

    resp = client.get("/v1/enforcement/lookup?plate=ENF100", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["plate"] == "ENF100"


def test_lookup_plate_not_found(client, make_user, auth_headers):
    make_user("enf_officer_notfound@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_notfound@test.com")

    resp = client.get("/v1/enforcement/lookup?plate=XXXXXX", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["data"] is None


def test_lookup_logs_enforcement_check(client, make_user, auth_headers, db):
    from app.models.enforcement import EnforcementCheck
    make_user("enf_officer_log@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_log@test.com")

    before = db.query(EnforcementCheck).count()
    client.get("/v1/enforcement/lookup?plate=LOGTEST", headers=headers)
    after = db.query(EnforcementCheck).count()
    assert after == before + 1


def test_parker_cannot_lookup(client, make_user, auth_headers):
    make_user("enf_parker_block@test.com", role="PARKER")
    headers = auth_headers("enf_parker_block@test.com")

    resp = client.get("/v1/enforcement/lookup?plate=ABC123", headers=headers)
    assert resp.status_code == 403


# ── Citations ─────────────────────────────────────────────────────────────────

def test_issue_citation(client, make_user, auth_headers):
    make_user("enf_officer_cite@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_cite@test.com")

    resp = client.post("/v1/enforcement/citations", headers=headers, json={
        "vehicle_plate": "CIT001",
        "zone": "B2",
        "violation_type": "No Valid Session",
        "fine_amount": 5000,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["vehicle_plate"] == "CIT001"
    assert data["paid"] is False
    assert data["fine_amount"] == 5000


def test_issue_citation_invalid_violation_type(client, make_user, auth_headers):
    make_user("enf_officer_badtype@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_badtype@test.com")

    resp = client.post("/v1/enforcement/citations", headers=headers, json={
        "vehicle_plate": "CIT002",
        "zone": "C3",
        "violation_type": "Made Up Violation",
    })
    assert resp.status_code == 400


def test_list_officer_citations(client, make_user, auth_headers):
    make_user("enf_officer_list@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_list@test.com")

    client.post("/v1/enforcement/citations", headers=headers, json={
        "vehicle_plate": "LST001", "zone": "D4", "violation_type": "Expired Session",
    })
    resp = client.get("/v1/enforcement/citations", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    plates = [c["vehicle_plate"] for c in resp.json()]
    assert "LST001" in plates


def test_officer_only_sees_own_citations(client, make_user, auth_headers):
    make_user("enf_off_a@test.com", role="ENFORCEMENT")
    make_user("enf_off_b@test.com", role="ENFORCEMENT")

    headers_a = auth_headers("enf_off_a@test.com")
    headers_b = auth_headers("enf_off_b@test.com")

    client.post("/v1/enforcement/citations", headers=headers_a, json={
        "vehicle_plate": "OFFA01", "zone": "A1", "violation_type": "No Permit",
    })

    # Officer B's citation list should not include officer A's citation
    resp = client.get("/v1/enforcement/citations", headers=headers_b)
    plates = [c["vehicle_plate"] for c in resp.json()]
    assert "OFFA01" not in plates


def test_get_violation_types(client, make_user, auth_headers):
    make_user("enf_officer_vtypes@test.com", role="ENFORCEMENT")
    headers = auth_headers("enf_officer_vtypes@test.com")

    resp = client.get("/v1/enforcement/violation-types", headers=headers)
    assert resp.status_code == 200
    types = resp.json()
    assert isinstance(types, list)
    assert "No Valid Session" in types


def test_parker_cannot_issue_citation(client, make_user, auth_headers):
    make_user("enf_parker_cite@test.com", role="PARKER")
    headers = auth_headers("enf_parker_cite@test.com")

    resp = client.post("/v1/enforcement/citations", headers=headers, json={
        "vehicle_plate": "BLOCK1", "zone": "A1", "violation_type": "No Valid Session",
    })
    assert resp.status_code == 403
