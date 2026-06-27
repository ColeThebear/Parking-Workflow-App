import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models.enforcement import Citation
from ..models.parking import ParkingSession
from ..models.token import TokenBalance, Transaction
from ..models.user import User, UserRole
from ..schemas.auth import AdminResetPasswordRequest, AdminResetPasswordResponse
from ..utils.dependencies import (
    require_admin,
    require_admin_citations,
    require_admin_full,
    require_admin_users,
)
from ..utils.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dashboard overview ────────────────────────────────────────────────────────

@router.get("/stats")
def get_admin_stats(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    active = (
        db.query(func.count(ParkingSession.id))
        .filter(
            ParkingSession.active.is_(True),
            or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now),
        )
        .scalar() or 0
    )

    total_users     = db.query(func.count(User.id)).scalar() or 0
    total_students  = db.query(func.count(User.id)).filter(User.role == UserRole.PARKER).scalar() or 0
    total_officers  = db.query(func.count(User.id)).filter(User.role == UserRole.ENFORCEMENT).scalar() or 0
    total_citations = db.query(func.count(Citation.id)).scalar() or 0
    unpaid_citations = db.query(func.count(Citation.id)).filter(Citation.paid.is_(False)).scalar() or 0

    return {
        "active_sessions":   active,
        "total_users":       total_users,
        "total_students":    total_students,
        "total_officers":    total_officers,
        "total_citations":   total_citations,
        "unpaid_citations":  unpaid_citations,
    }


# ── All citations (admin view) ─────────────────────────────────────────────────

@router.get("/citations")
def get_all_citations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin_citations),
    db: Session = Depends(get_db),
):
    citations = (
        db.query(Citation)
        .options(joinedload(Citation.officer), joinedload(Citation.student))
        .order_by(Citation.issued_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id":             c.id,
            "plate":          c.vehicle_plate,
            "zone":           c.zone,
            "violation_type": c.violation_type,
            "fine_amount":    c.fine_amount,
            "issued_at":      c.issued_at.isoformat(),
            "paid":           c.paid,
            "appealed":       c.appealed,
            "officer_email":  c.officer.email,
            "student_email":  c.student.email if c.student else None,
        }
        for c in citations
    ]


@router.patch("/citations/{citation_id}/paid")
def mark_citation_paid(
    citation_id: int,
    _: User = Depends(require_admin_citations),
    db: Session = Depends(get_db),
):
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found.")
    citation.paid = True
    db.commit()
    return {"success": True}


# ── All users ─────────────────────────────────────────────────────────────────

@router.get("/users")
def get_all_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(require_admin_users),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).offset(offset).limit(limit).all()
    return [
        {"id": u.id, "email": u.email, "role": u.role.value}
        for u in users
    ]


# ── Balance management (admin can credit accounts) ────────────────────────────

class CreditRequest(BaseModel):
    user_id:     int
    amount:      int          # cents
    description: str = "Admin credit"


@router.post("/balance/credit")
def admin_credit(
    payload: CreditRequest,
    current_user: User = Depends(require_admin_full),
    db: Session = Depends(get_db),
):
    bal = (
        db.query(TokenBalance)
        .filter(TokenBalance.user_id == payload.user_id)
        .with_for_update()
        .first()
    )
    if not bal:
        raise HTTPException(status_code=404, detail="No balance account found for that user.")

    bal.balance += payload.amount
    bal.version += 1
    db.add(Transaction(
        balance_id=bal.id,
        amount=payload.amount,
        description=payload.description,
        tx_type="ADMIN",
    ))
    db.commit()
    return {"balance": bal.balance}


# ── Password reset (admin resets a user's password) ──────────────────────────

@router.post("/reset-password", response_model=AdminResetPasswordResponse)
def admin_reset_password(
    payload: AdminResetPasswordRequest,
    _: User = Depends(require_admin_full),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    temp_password = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temp_password)
    db.commit()

    return AdminResetPasswordResponse(
        user_id=user.id,
        email=user.email,
        temp_password=temp_password,
    )
