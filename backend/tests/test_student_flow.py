from app.models.user import User
from app.utils.security import hash_password

def test_student_start_parking(client, db):
    user = User(
        email="student_flow@test.com",
        password_hash = hash_password("123"),
        role="PARKER"
    )
    db.add(user)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "student_flow@test.com",
        "password": "123"
    })
    token = login.json()["access_token"]

    response = client.post(
        "/parking/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"vehicle_plate": "ABC123", "zone": "A1"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_plate"] == "ABC123"
    assert data["zone"] == "A1"
