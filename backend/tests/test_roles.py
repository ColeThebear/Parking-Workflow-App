from app.models.user import User
from app.utils.security import hash_password


def test_parker_cannot_access_enforcement(client, db, make_user, auth_headers):
    make_user("parker_roles@test.com", role="PARKER")
    headers = auth_headers("parker_roles@test.com")

    response = client.get("/enforcement/lookup?plate=ABC123", headers=headers)
    assert response.status_code == 403


def test_enforcement_can_access_enforcement(client, db, make_user, auth_headers):
    make_user("enforcer_roles@test.com", role="ENFORCEMENT")
    headers = auth_headers("enforcer_roles@test.com")

    response = client.get("/enforcement/lookup?plate=ABC123", headers=headers)
    assert response.status_code == 200
