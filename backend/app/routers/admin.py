from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enforcement import Citation
from ..models.parking import ParkingSession
from ..models.token import TokenBalance, Transaction
from ..models.user import User, UserRole
from ..utils.dependencies import require_admin

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
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    citations = (
        db.query(Citation)
        .order_by(Citation.issued_at.desc())
        .limit(200)
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
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id).all()
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
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    bal = db.query(TokenBalance).filter(TokenBalance.user_id == payload.user_id).first()
    if not bal:
        raise HTTPException(status_code=404, detail="No balance account found for that user.")
    bal.balance += payload.amount
    db.add(Transaction(
        balance_id=bal.id,
        amount=payload.amount,
        description=payload.description,
        tx_type="ADMIN",
    ))
    db.commit()
    return {"balance": bal.balance}
