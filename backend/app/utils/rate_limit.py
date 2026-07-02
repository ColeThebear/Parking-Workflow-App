import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Set RATELIMIT_ENABLED=0 in the environment to disable rate limiting.
# Used in the test suite (conftest.py sets this before importing the app)
# so TestClient's shared remote address doesn't exhaust the per-minute caps.
_enabled = os.environ.get("RATELIMIT_ENABLED", "1") != "0"

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
