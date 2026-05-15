from sqlalchemy import Column, Integer, String, Enum, Boolean
from ..database import Base
import enum


class UserRole(str, enum.Enum):
    PARKER      = "PARKER"
    OPERATOR    = "OPERATOR"
    ENFORCEMENT = "ENFORCEMENT"
    ADMIN       = "ADMIN"
    GUEST       = "GUEST"


class User(Base):
    __tablename__ = "users"

    id                       = Column(Integer, primary_key=True, index=True)
    email                    = Column(String,  unique=True, index=True)
    password_hash            = Column(String)
    role                     = Column(Enum(UserRole), default=UserRole.PARKER)
    # Display name (optional — populated via CSV import or guest registration)
    name                     = Column(String, nullable=True)
    # Admins only: full_admin | events_admin | citations_admin | reporting_admin
    admin_permission         = Column(String, nullable=True)
    # Set to True when an operator force-ends a student's session.
    # Reset to False the next time the student logs in (after showing the alert).
    terminated_by_operator   = Column(Boolean, default=False, nullable=False,
                                      server_default="false")
