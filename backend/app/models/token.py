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


class RevokedToken(Base):
    """SHA-256 hashes of revoked refresh tokens.

    Inserted on logout; checked on every /auth/refresh call.
    Rows whose expires_at has passed are safe to prune — the JWT itself
    would be rejected by the signature check anyway.
    """
    __tablename__ = "revoked_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), default=_utcnow)
