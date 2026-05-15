from . import user, parking, enforcement, vehicle, token, guest   # noqa: F401
# Importing all model modules here ensures SQLAlchemy registers them with Base
# before create_all() is called in main.py.
