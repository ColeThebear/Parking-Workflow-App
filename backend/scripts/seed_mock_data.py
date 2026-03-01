import requests
from datetime import datetime, timedelta

BASE = "http://localhost:8000"

users = [
    {"email": "student1@suny.edu", "password": "Test123!", "role": "PARKER"},
    {"email": "student2@suny.edu", "password": "Test123!", "role": "PARKER"},
    {"email": "officer1@suny.edu", "password": "Test123!", "role": "ENFORCEMENT"},
    {"email": "operator@suny.edu", "password": "Test123!", "role": "OPERATOR"},
]

# Register users
for u in users:
    try:
        requests.post(f"{BASE}/auth/register", json=u)
    except:
        pass

# Login as student1
token = requests.post(f"{BASE}/auth/login", json=users[0]).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create parking sessions
plates = ["ABC123", "SUNY456", "PARK789", "NYS102"]
zones = ["Student Lot A", "Student Lot B", "Faculty Lot", "Visitor Lot"]

for plate, zone in zip(plates, zones):
    requests.post(
        f"{BASE}/parking/start",
        json={"vehicle_plate": plate, "zone": zone},
        headers=headers
    )

print("Mock data seeded successfully.")