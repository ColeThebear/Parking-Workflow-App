from app.models.user import User
from app.utils.security import hash_password
from app.models.parking import ParkingSession


def test_enforcement_lookup_active_parking(client, db):
    parker = User(
        email="parker_enforcement@test.com",
        password_hash=hash_password("Test123!"),
        role="PARKER"
    )
    enforcer = User(
        email="enforcer_enforcement@test.com",
        password_hash=hash_password("Test123!"),
        role="ENFORCEMENT"
    )
    db.add(parker)
    db.add(enforcer)
    db.commit()

    # Create active parking session with a unique plate
    session = ParkingSession(
        user_id=parker.id,
        vehicle_plate="ENF001",
        zone="A1",
        active=True
    )
    db.add(session)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "enforcer_enforcement@test.com",
        "password": "Test123!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/enforcement/lookup?plate=ENF001",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["plate"] == "ENF001"
