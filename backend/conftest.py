import pytest

@pytest.fixture
def user_fixture():
    return {"username": "test_user"}