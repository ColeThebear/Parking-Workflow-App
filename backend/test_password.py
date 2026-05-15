import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(here))

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import verify_password

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == "student1@suny.edu").first()
    if user:
        print(f"User found: {user.email}")
        print(f"Password hash: {user.password_hash[:50]}...")

        # Test password verification
        test_password = "password123"
        is_valid = verify_password(test_password, user.password_hash)
        print(f"Password 'password123' valid: {is_valid}")

        # Test with Test123!
        test_password2 = "Test123!"
        is_valid2 = verify_password(test_password2, user.password_hash)
        print(f"Password 'Test123!' valid: {is_valid2}")
    else:
        print("User not found")
finally:
    db.close()