from app.models.user import User
from app.utils.security import hash_password
from app.models.parking import ParkingSession


def test_enforcement_lookup_active_parking(client, db):
    parker = User(
        email="parker_enforcement@test.com",
        password_hash = hash_password("123"),
        role="PARKER"
    )
    enforcer = User(
        email="enforcer_enforcement@test.com",
        password_hash = hash_password("123"),
        role="ENFORCEMENT"
    )
    db.add(parker)
    db.add(enforcer)
    db.commit()

    # Create active parking session
    session = ParkingSession(
        user_id=parker.id,
        vehicle_plate="ABC123",
        zone="A1",
        active=True
    )
    db.add(session)
    db.commit()

    # Login as enforcement
    login = client.post("/auth/login", json={
        "email": "enforcer_enforcement@test.com",
        "password": "123"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/parking/plate/ABC123",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["vehicle_plate"] == "ABC123"
    assert data[0]["active"] is True