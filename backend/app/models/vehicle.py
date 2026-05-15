from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RegisteredVehicle(Base):
    """Vehicle plates registered to a student account.
    Used for duplicate detection during CSV import."""
    __tablename__ = "registered_vehicles"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    plate       = Column(String, unique=True, nullable=False, index=True)
    created_at  = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User")
