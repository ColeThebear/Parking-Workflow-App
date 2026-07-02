import os
import sys
import time

# MUST be set before any app imports — rate_limit.py reads this at construction
# time, so the Limiter is created with enabled=False for the entire test session.
# TestClient uses a fixed remote address ('testclient'), so without this every
# test that calls /auth/login exhausts the 5/minute cap and gets 429.
os.environ["RATELIMIT_ENABLED"] = "0"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, engine as db_engine
from app.utils.rate_limit import limiter


# Replace _check_request_limit with a no-op at module load time.
# The @limiter.limit() decorator calls await self._check_request_limit(...)
# at request time; an instance attribute shadows the class method, so this
# bypasses rate enforcement regardless of which slowapi version is installed.
async def _noop_rate_limit_check(*args, **kwargs) -> None:
    return

limiter._check_request_limit = _noop_rate_limit_check

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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
