from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EnforcementCheck(Base):
    """Logged every time an enforcement officer looks up a plate."""
    __tablename__ = "enforcement_checks"

    id              = Column(Integer, primary_key=True, index=True)
    officer_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehicle_plate   = Column(String, nullable=False, index=True)
    session_found   = Column(Boolean, nullable=False)   # True = active session was found
    checked_at      = Column(DateTime(timezone=True), default=_utcnow)

    officer = relationship("User", foreign_keys=[officer_id])


class Citation(Base):
    """Parking violation citation issued by enforcement."""
    __tablename__ = "citations"

    id              = Column(Integer, primary_key=True, index=True)
    officer_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=True)   # None = unregistered vehicle
    vehicle_plate   = Column(String, nullable=False, index=True)
    zone            = Column(String, nullable=False)
    violation_type  = Column(String, nullable=False)   # e.g. "No Valid Session", "Expired Session"
    fine_amount     = Column(Integer, nullable=False, default=0)  # cents, e.g. 5000 = $50.00
    notes           = Column(Text, nullable=True)
    issued_at       = Column(DateTime(timezone=True), default=_utcnow)
    paid            = Column(Boolean, default=False, nullable=False)
    appealed        = Column(Boolean, default=False, nullable=False)

    officer = relationship("User", foreign_keys=[officer_id])
    student = relationship("User", foreign_keys=[user_id])
