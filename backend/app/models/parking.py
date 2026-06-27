from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index, CheckConstraint
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
    __table_args__ = (
        Index("ix_session_plate_active", "vehicle_plate", "active"),
    )

    id            = Column(Integer,  primary_key=True, index=True)
    vehicle_plate = Column(String,   index=True, nullable=False)
    zone          = Column(String,   nullable=False)
    started_at    = Column(DateTime(timezone=True), default=_utcnow)
    expires_at    = Column(DateTime(timezone=True), nullable=True)   # NULL = no expiry (legacy rows)
    ended_at      = Column(DateTime(timezone=True), nullable=True)
    active        = Column(Boolean,  default=True,  nullable=False)
    user_id       = Column(Integer,  ForeignKey("users.id"), nullable=True)

    user = relationship("User", lazy="select")  # Load user only when accessed


class HistoricParkingSession(Base):
    __tablename__ = "historic_parking_sessions"
    __table_args__ = (
        CheckConstraint("user_type IN ('STUDENT', 'GUEST', 'UNREGISTERED')", name="ck_historic_user_type"),
        CheckConstraint("session_type IN ('STANDARD', 'PERMIT', 'EVENT')", name="ck_historic_session_type"),
        CheckConstraint("payment_type IN ('TOKEN', 'CASH', 'CARD', 'FREE')", name="ck_historic_payment_type"),
        CheckConstraint("enforcement_status IN ('NONE', 'CHECKED', 'CITED')", name="ck_historic_enforcement_status"),
    )

    id                 = Column(Integer,  primary_key=True, index=True)
    vehicle_plate      = Column(String,   index=True, nullable=False)
    zone               = Column(String,   nullable=False)
    started_at         = Column(DateTime(timezone=True), nullable=False)
    ended_at           = Column(DateTime(timezone=True), nullable=True)
    duration_minutes   = Column(Integer,  nullable=True)
    # STUDENT / GUEST / UNREGISTERED
    user_type          = Column(String,   nullable=False, default="STUDENT")
    # STANDARD / PERMIT / EVENT
    session_type       = Column(String,   nullable=False, default="STANDARD")
    # TOKEN / CASH / CARD / FREE
    payment_type       = Column(String,   nullable=False, default="FREE")
    # NONE / CHECKED / CITED
    enforcement_status = Column(String,   nullable=False, default="NONE")
    notes              = Column(String,   nullable=True)
    user_id            = Column(Integer,  ForeignKey("users.id"), nullable=True)
    imported_at        = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", lazy="select")
