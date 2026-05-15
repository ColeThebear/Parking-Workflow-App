"""
Test configuration template.

Copy this file to conftest.py and set DATABASE_URL to your local test database.
Never commit conftest.py — it is gitignored because it contains local credentials.

Setup:
    1. cp backend/tests/conftest.example.py backend/tests/conftest.py
    2. Edit conftest.py and replace the DATABASE_URL placeholder with your credentials.
    3. Or export DATABASE_URL in your shell before running pytest.
"""
import os

# MUST be set before importing app.main or app.database
# Replace with your local test database credentials.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://<user>:<password>@localhost:5432/<test_db>",
)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.database import get_db

engine = create_engine(os.environ["DATABASE_URL"])
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def wait_for_db():
    for _ in range(10):
        try:
            conn = engine.connect()
            conn.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Test DB did not become ready")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.main import seed_default_users
    seed_default_users()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
