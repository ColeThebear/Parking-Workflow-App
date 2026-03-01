from sqlalchemy import Column, Integer, String, Enum
from ..database import Base
import enum

class UserRole(str, enum.Enum):
    PARKER = "PARKER"
    OPERATOR = "OPERATOR"
    ENFORCEMENT = "ENFORCEMENT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(Enum(UserRole), default=UserRole.PARKER)