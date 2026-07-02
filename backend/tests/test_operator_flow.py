from app.models.user import User
from app.utils.security import hash_password
from app.models.parking import ParkingSession


def test_operator_dashboard(client, db):
    operator = User(
        email="operator_test@test.com",
        password_hash=hash_password("Test123!"),
        role="OPERATOR"
    )
    parker = User(
        email="parker_operator@test.com",
        password_hash=hash_password("Test123!"),
        role="PARKER"
    )
    db.add(operator)
    db.add(parker)
    db.commit()

    # Create an active session with a unique plate
    session = ParkingSession(
        user_id=parker.id,
        vehicle_plate="OPR001",
        zone="A1",
        active=True
    )
    db.add(session)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "operator_test@test.com",
        "password": "Test123!"
    })
    token = login.json()["access_token"]

    # Stats endpoint
    response = client.get(
        "/operator/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data

    # Active sessions endpoint
    resp_active = client.get(
        "/operator/sessions/active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_active.status_code == 200
    active_data = resp_active.json()
    assert isinstance(active_data, list)
    plates = [s["plate"] for s in active_data]
    assert "OPR001" in plates
