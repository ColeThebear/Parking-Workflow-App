from app.models.user import User
from app.utils.security import hash_password


def test_parker_cannot_access_enforcement(client, db):
    user = User(
        email="parker_roles@test.com",
        password_hash=hash_password("Test123!"),
        role="PARKER"
    )
    db.add(user)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "parker_roles@test.com",
        "password": "Test123!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/enforcement/lookup?plate=ABC123",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_enforcement_can_access_enforcement(client, db):
    user = User(
        email="enforcer_roles@test.com",
        password_hash=hash_password("Test123!"),
        role="ENFORCEMENT"
    )
    db.add(user)
    db.commit()

    login = client.post("/auth/login", json={
        "email": "enforcer_roles@test.com",
        "password": "Test123!"
    })
    token = login.json()["access_token"]

    response = client.get(
        "/enforcement/lookup?plate=ABC123",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
