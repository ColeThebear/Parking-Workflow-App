from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


def _utcnow() -> datetime:
    """
    Timezone-aware UTC timestamp.
    Replaces the deprecated datetime.utcnow() (removed in Python 3.12).
    """
    return datetime.now(timezone.utc)


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id            = Column(Integer,  primary_key=True, index=True)
    vehicle_plate = Column(String,   index=True, nullable=False)
    zone          = Column(String,   nullable=False)
    started_at    = Column(DateTime(timezone=True), default=_utcnow)
    expires_at    = Column(DateTime(timezone=True), nullable=True)   # NULL = no expiry (legacy rows)
    ended_at      = Column(DateTime(timezone=True), nullable=True)
    active        = Column(Boolean,  default=True,  nullable=False)
    user_id       = Column(Integer,  ForeignKey("users.id"), nullable=True)

    user = relationship("User", lazy="select")  # Load user only when accessed
