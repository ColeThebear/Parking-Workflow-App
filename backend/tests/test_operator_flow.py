from app.models.parking import ParkingSession


def test_operator_dashboard(client, db, make_user, auth_headers):
    parker   = make_user("parker_operator@test.com", role="PARKER")
    operator = make_user("operator_test@test.com", role="OPERATOR")

    session = ParkingSession(
        user_id=parker.id,
        vehicle_plate="OPR001",
        zone="A1",
        active=True,
    )
    db.add(session)
    db.commit()

    headers = auth_headers("operator_test@test.com")

    response = client.get("/operator/stats", headers=headers)
    assert response.status_code == 200
    assert "active_sessions" in response.json()

    resp_active = client.get("/operator/sessions/active", headers=headers)
    assert resp_active.status_code == 200
    plates = [s["plate"] for s in resp_active.json()]
    assert "OPR001" in plates
