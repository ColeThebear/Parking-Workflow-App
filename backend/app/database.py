from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,     # Verify connection health before use — prevents
                            # "SSL connection has been closed unexpectedly"
                            # errors after the DB is idle for a few minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# declarative_base() is deprecated in SQLAlchemy 2.0 in favour of:
#   class Base(DeclarativeBase): pass
# It still works in 2.0 with a warning. Migrate after the demo if needed.
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
