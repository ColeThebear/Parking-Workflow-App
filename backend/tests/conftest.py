import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, engine as db_engine
from app.utils.rate_limit import limiter

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Wait for DB, create all tables once, seed demo users. Drops all on teardown."""
    for attempt in range(10):
        try:
            with db_engine.connect():
                break
        except Exception:
            if attempt == 9:
                raise RuntimeError("Test database did not become ready in time.")
            time.sleep(1)

    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    from app.main import seed_default_users
    seed_default_users()
    yield
    Base.metadata.drop_all(bind=db_engine)


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
        yield db

    # Reset in-memory rate limit counters so each test starts clean.
    # TestClient uses a fixed remote address, so without this tests that call
    # rate-limited endpoints back-to-back would exhaust the per-minute caps.
    limiter._storage.reset()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


# ── Shared test helpers ───────────────────────────────────────────────────────

@pytest.fixture()
def make_user(db):
    """Factory fixture — creates a User row and returns it."""
    from app.models.user import User
    from app.utils.security import hash_password

    def _make(email: str, role: str = "PARKER", password: str = "Test123!",
              admin_permission: str | None = None) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            admin_permission=admin_permission,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers(client):
    """Factory fixture — returns Bearer auth headers for a given email/password."""
    def _headers(email: str, password: str = "Test123!") -> dict:
        resp = client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200, f"Login failed for {email}: {resp.json()}"
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _headers
