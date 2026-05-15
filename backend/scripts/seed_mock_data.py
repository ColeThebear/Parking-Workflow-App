"""Development helper that seeds the database with mock users and parking
sessions.  The previous iteration relied on firing HTTP requests at
`localhost:8000` which would silently fail if the API wasn't ready; this
version uses SQLAlchemy directly so it's deterministic and can be run long
before the backend container starts.

Run it from the backend directory (``python scripts/seed_mock_data.py``) and
make sure your ``DATABASE_URL`` environment variable points at the same
database that the application uses.
"""

import os
import sys

# ensure the parent package is importable when invoking this script directly
here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(here, "..")))

from app.database import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.utils.security import hash_password

# make sure tables exist before inserting
Base.metadata.create_all(bind=engine)

users = [
    {"email": "student1@suny.edu", "password": "Test123!", "role": UserRole.PARKER},
    {"email": "student2@suny.edu", "password": "Test123!", "role": UserRole.PARKER},
    {"email": "officer1@suny.edu", "password": "Test123!", "role": UserRole.ENFORCEMENT},
    {"email": "operator@suny.edu", "password": "Test123!", "role": UserRole.OPERATOR},
]

# insert users directly into the database and avoid duplicates
print("Seeding mock users directly into database...")
session = SessionLocal()
try:
    for u in users:
        existing = session.query(User).filter(User.email == u["email"]).first()
        if existing:
            print(f" - user {u['email']} already exists, skipping")
            continue
        session.add(
            User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            )
        )
    session.commit()
    print("User seeding complete.")
finally:
    session.close()

# parking sessions can still be generated via the API if desired; we
# dropped the HTTP portion to keep the script focused on users.
