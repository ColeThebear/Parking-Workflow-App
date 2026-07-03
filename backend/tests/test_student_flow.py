def test_student_start_parking(client, make_user, auth_headers):
    make_user("student_flow@test.com")
    headers = auth_headers("student_flow@test.com")

    response = client.post(
        "/student/start",
        headers=headers,
        json={"plate": "STU001", "zone": "A1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["plate"] == "STU001"
    assert data["zone"] == "A1"
