from app.models.user import User


def test_default_users_created(client, db):
    # the application startup logic seeds a handful of known accounts when
    # the users table is empty; make sure the fixture triggers that behavior.
    users = db.query(User).all()
    # at least the four configured defaults should exist
    assert len(users) >= 4
    emails = {u.email for u in users}
    assert "student1@suny.edu" in emails
    assert "operator@suny.edu" in emails
