from app.models.user import User
from app.utils.security import hash_password
from app.models.parking import ParkingSession


def test_operator_dashboard(client, db):
    operator = User(
        email="operator_test@test.com",
        password_hash = hash_password("123"),
        role="OPERATOR"
    )
    parker = User(
        email="parker_operator@test.com",
        password_hash = hash_password("123"),
        role="PARKER"
    )
    db.add(operator)
    db.add(parker)
    db.commit()

    # Create some parking sessions
    session1 = ParkingSession(
        user_id=parker.id,
        vehicle_plate="ABC123",
        zone="A1",
        active=True
    )
    session2 = ParkingSession(
        user_id=parker.id,
        vehicle_plate="XYZ789",
        zone="B2",
        active=False
    )
    db.add(session1)
    db.add(session2)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "operator_test@test.com",
        "password": "123"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/parking",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Just check that we got a response from the operator
    assert isinstance(data, (list, dict))

    # verify active-specific endpoint filters correctly
    resp_active = client.get(
        "/parking/active",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_active.status_code == 200
    active_data = resp_active.json()
    # only one of the sessions we created was active
    assert isinstance(active_data, list)
    assert len(active_data) == 1
    assert active_data[0]["active"] is True