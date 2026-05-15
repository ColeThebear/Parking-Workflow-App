import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(here))

from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    for u in users:
        hash_preview = u.password_hash[:30] if u.password_hash else "None"
        print(f"{u.email}: {hash_preview}...")
finally:
    db.close()
