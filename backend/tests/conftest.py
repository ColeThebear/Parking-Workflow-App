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
