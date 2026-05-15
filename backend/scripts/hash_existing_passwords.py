"""Hash all existing plain text passwords in the database with Argon2."""

import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(here, "..")))

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

db = SessionLocal()
try:
    users = db.query(User).all()
    updated = 0
    
    for user in users:
        # Check if password is already hashed (starts with $argon2)
        if user.password_hash and not user.password_hash.startswith("$argon2"):
            # Plain text password detected - hash it
            print(f"Hashing plain text password for {user.email}")
            user.password_hash = hash_password(user.password_hash)
            updated += 1
    
    if updated > 0:
        db.commit()
        print(f"Successfully hashed {updated} password(s)")
    else:
        print("All passwords are already properly hashed")
finally:
    db.close()
