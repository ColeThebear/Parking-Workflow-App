from datetime import datetime, timezone, timedelta
from app.models.parking import ParkingSession


def test_enforcement_lookup_active_parking(client, db, make_user, auth_headers):
    parker   = make_user("parker_enforcement@test.com")
    enforcer = make_user("enforcer_enforcement@test.com", role="ENFORCEMENT")

    now = datetime.now(timezone.utc)
    session = ParkingSession(
        user_id=parker.id,
        vehicle_plate="ENF001",
        zone="A1",
        active=True,
        started_at=now,
        expires_at=now + timedelta(hours=1),
    )
    db.add(session)
    db.commit()

    headers = auth_headers("enforcer_enforcement@test.com")
    response = client.get("/enforcement/lookup?plate=ENF001", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["plate"] == "ENF001"
