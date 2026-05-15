import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(here))

from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"Found {len(users)} users:")
    for u in users:
        print(f"  {u.email}: {u.role}")
finally:
    db.close()