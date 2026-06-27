from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from ..database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TokenBalance(Base):
    """Dollar balance (stored in cents) for a student account."""
    __tablename__ = "token_balances"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance     = Column(Integer, nullable=False, default=0)  # cents
    version     = Column(Integer, nullable=False, default=1, server_default="1")
    updated_at  = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user         = relationship("User")
    transactions = relationship("Transaction", back_populates="balance_account",
                                order_by="Transaction.created_at.desc()")


class Transaction(Base):
    """Credit/debit record for a student's token balance."""
    __tablename__ = "transactions"

    id              = Column(Integer, primary_key=True, index=True)
    balance_id      = Column(Integer, ForeignKey("token_balances.id"), nullable=False)
    amount          = Column(Integer, nullable=False)   # positive = credit, negative = debit (cents)
    description     = Column(String, nullable=False)
    tx_type         = Column(String, nullable=False)    # "TOP_UP" | "SESSION" | "PERMIT" | "ADMIN"
    created_at      = Column(DateTime(timezone=True), default=_utcnow)

    balance_account = relationship("TokenBalance", back_populates="transactions")
