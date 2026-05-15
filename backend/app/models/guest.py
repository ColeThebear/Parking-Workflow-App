from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


def _next_august() -> datetime:
    """Return the next upcoming August 1st at 00:00 UTC."""
    now = datetime.now(timezone.utc)
    candidate = datetime(now.year, 8, 1, tzinfo=timezone.utc)
    if candidate <= now:
        candidate = datetime(now.year + 1, 8, 1, tzinfo=timezone.utc)
    return candidate


class GuestProfile(Base):
    """
    Extra profile data for GUEST-role users.
    One row per guest, created alongside the User record at registration.

    expires_at   Auto-set to the next upcoming August 1st.
                 Expired guests are rejected at login.
    limited_access  Always True for self-registered guests.
                    Can be False if manually elevated by an admin.
    """
    __tablename__ = "guest_profiles"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                            unique=True, nullable=False, index=True)
    name           = Column(String, nullable=False)
    license_plate  = Column(String, nullable=True)
    expires_at     = Column(DateTime(timezone=True), nullable=False,
                            default=_next_august)
    limited_access = Column(Boolean, default=True, nullable=False,
                            server_default="true")

    user = relationship("User", backref="guest_profile", foreign_keys=[user_id])
