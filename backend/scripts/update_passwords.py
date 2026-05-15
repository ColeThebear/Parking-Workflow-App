"""Update existing user passwords with proper hashes."""

import os
import sys

# ensure the parent package is importable when invoking this script directly
here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(here, "..")))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password

users = [
    {"email": "student1@suny.edu", "password": "Test123!", "role": UserRole.PARKER},
    {"email": "student2@suny.edu", "password": "Test123!", "role": UserRole.PARKER},
    {"email": "officer1@suny.edu", "password": "Test123!", "role": UserRole.ENFORCEMENT},
    {"email": "operator@suny.edu", "password": "Test123!", "role": UserRole.OPERATOR},
]

session = SessionLocal()
try:
    for u in users:
        user = session.query(User).filter(User.email == u["email"]).first()
        if user:
            user.password_hash = hash_password(u["password"])
            print(f"Updated password for {u['email']}")
    session.commit()
    print("Password update complete.")
finally:
    session.close()