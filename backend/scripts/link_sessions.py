"""Link existing parking sessions to users based on the seed data."""

import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(here))

from app.database import SessionLocal
from app.models.parking import ParkingSession
from app.models.user import User

# Mapping of license plates to users based on seed data
plate_to_user = {
    "ABC123": "student1@suny.edu",
    "SUNY456": "student2@suny.edu",
    "PARK789": "officer1@suny.edu",  # This was in faculty lot, maybe should be operator?
    "NYS102": "operator@suny.edu",  # This was in visitor lot
}

db = SessionLocal()
try:
    for plate, email in plate_to_user.items():
        user = db.query(User).filter(User.email == email).first()
        if user:
            session = db.query(ParkingSession).filter(ParkingSession.vehicle_plate == plate).first()
            if session and session.user_id is None:
                session.user_id = user.id
                print(f"Linked {plate} to {email} (user_id: {user.id})")
    
    db.commit()
    print("Parking session linking complete.")
finally:
    db.close()