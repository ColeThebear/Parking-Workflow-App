import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.enforcement import EnforcementCheck, Citation
from ..models.parking import ParkingSession
from ..models.token import TokenBalance
from ..models.user import User, UserRole
from ..models.vehicle import RegisteredVehicle
from ..schemas.parking import (
    ParkingSessionOut,
    StudentSearchResult,
    EndSessionRequest,
    EndSessionResponse,
)
from ..utils.dependencies import require_operator
from ..utils.security import hash_password

router = APIRouter(prefix="/operator", tags=["operator"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session_to_out(s: ParkingSession) -> ParkingSessionOut:
    return ParkingSessionOut(
        session_id=s.id,
        plate=s.vehicle_plate,
        zone=s.zone,
        start_time=s.started_at,
        expires_at=s.expires_at,
    )


def _is_live(s: ParkingSession, now: datetime) -> bool:
    return s.active and (s.expires_at is None or s.expires_at > now)


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    active_count = (
        db.query(func.count(ParkingSession.id))
        .filter(
            ParkingSession.active.is_(True),
            or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now),
        )
        .scalar() or 0
    )

    today_count = (
        db.query(func.count(ParkingSession.id))
        .filter(func.date(ParkingSession.started_at) == func.current_date())
        .scalar() or 0
    )

    check_count = (
        db.query(func.count(EnforcementCheck.id))
        .filter(func.date(EnforcementCheck.checked_at) == func.current_date())
        .scalar() or 0
    )

    violation_count = (
        db.query(func.count(Citation.id))
        .filter(func.date(Citation.issued_at) == func.current_date())
        .scalar() or 0
    )

    return {
        "active_sessions":      active_count,
        "total_sessions_today": today_count,
        "enforcement_checks":   check_count,
        "violations":           violation_count,
    }


# ── Active sessions ───────────────────────────────────────────────────────────

@router.get("/sessions/active")
def get_active_sessions(
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(ParkingSession)
        .filter(
            ParkingSession.active.is_(True),
            or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now),
        )
        .order_by(ParkingSession.started_at.desc())
        .all()
    )
    return [
        {
            "session_id":   s.id,
            "plate":        s.vehicle_plate,
            "zone":         s.zone,
            "start_time":   s.started_at.isoformat() if s.started_at else None,
            "expires_at":   s.expires_at.isoformat()  if s.expires_at  else None,
            "student_email": s.user.email if s.user else None,
        }
        for s in sessions
    ]


# ── Today's sessions ──────────────────────────────────────────────────────────

@router.get("/sessions/today")
def get_todays_sessions(
    zone:  Optional[str] = Query(None),
    plate: Optional[str] = Query(None),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    q = (
        db.query(ParkingSession)
        .filter(func.date(ParkingSession.started_at) == func.current_date())
    )
    if zone:
        q = q.filter(ParkingSession.zone == zone)
    if plate:
        q = q.filter(ParkingSession.vehicle_plate.ilike(f"%{plate.upper()}%"))

    sessions = q.order_by(ParkingSession.started_at.desc()).all()
    return [
        {
            "session_id":    s.id,
            "plate":         s.vehicle_plate,
            "zone":          s.zone,
            "start_time":    s.started_at.isoformat() if s.started_at else None,
            "ended_at":      s.ended_at.isoformat()    if s.ended_at    else None,
            "active":        s.active,
            "student_email": s.user.email if s.user else None,
        }
        for s in sessions
    ]


# ── Enforcement checks today ───────────────────────────────────────────────────

@router.get("/enforcement/checks")
def get_enforcement_checks(
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    checks = (
        db.query(EnforcementCheck)
        .filter(func.date(EnforcementCheck.checked_at) == func.current_date())
        .order_by(EnforcementCheck.checked_at.desc())
        .all()
    )
    return [
        {
            "id":           c.id,
            "plate":        c.vehicle_plate,
            "session_found": c.session_found,
            "checked_at":   c.checked_at.isoformat(),
            "officer":      c.officer.email,
        }
        for c in checks
    ]


# ── Violations today ──────────────────────────────────────────────────────────

@router.get("/enforcement/violations")
def get_violations(
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    citations = (
        db.query(Citation)
        .filter(func.date(Citation.issued_at) == func.current_date())
        .order_by(Citation.issued_at.desc())
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
            "officer":        c.officer.email,
            "student_email":  c.student.email if c.student else None,
        }
        for c in citations
    ]


# ── Student search ────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[StudentSearchResult])
def search_students(
    query: str = Query(..., min_length=1),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    term = f"%{query.strip().lower()}%"

    email_ids: set[int] = {
        row.id for row in
        db.query(User.id)
        .filter(User.role == UserRole.PARKER, func.lower(User.email).like(term))
        .all()
    }

    plate_ids: set[int] = {
        row.user_id for row in
        db.query(ParkingSession.user_id)
        .filter(
            ParkingSession.user_id.isnot(None),
            func.lower(ParkingSession.vehicle_plate).like(term),
        )
        .distinct().all()
        if row.user_id is not None
    }

    user_ids = list(email_ids | plate_ids)[:10]
    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    now   = datetime.now(timezone.utc)

    results = []
    for user in users:
        sessions = (
            db.query(ParkingSession)
            .filter(ParkingSession.user_id == user.id)
            .order_by(ParkingSession.started_at.desc())
            .limit(10).all()
        )
        active = next(
            (s for s in sessions if s.active and (s.expires_at is None or s.expires_at > now)),
            None,
        )
        results.append(StudentSearchResult(
            user_id=user.id,
            email=user.email,
            active_session=_session_to_out(active) if active else None,
            recent_sessions=[_session_to_out(s) for s in sessions],
        ))
    return results


# ── End session ───────────────────────────────────────────────────────────────

@router.post("/end-session", response_model=EndSessionResponse)
def operator_end_session(
    payload: EndSessionRequest,
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    session = db.query(ParkingSession).filter(ParkingSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if not session.active:
        raise HTTPException(status_code=400, detail="Session is already ended.")

    session.active   = False
    session.ended_at = datetime.now(timezone.utc)

    if session.user_id:
        student = db.query(User).filter(User.id == session.user_id).first()
        if student:
            student.terminated_by_operator = True

    db.commit()
    return EndSessionResponse(success=True, message="Session ended successfully.")


# ── CSV Student Import ────────────────────────────────────────────────────────

class ImportRow(BaseModel):
    row:     int
    email:   str
    plate:   Optional[str]
    reason:  str


class ImportResult(BaseModel):
    added:      int
    duplicates: list[ImportRow]
    errors:     list[ImportRow]


@router.post("/import-students", response_model=ImportResult)
async def import_students(
    file: UploadFile = File(...),
    current_user: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file to bulk-create student accounts.

    Expected CSV columns (header required):
        email, plate (optional), password (optional)

    Duplicate detection:
        - email already in users table → skip
        - plate already in registered_vehicles → skip
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")   # handle BOM from Excel exports
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or "email" not in [f.lower() for f in reader.fieldnames]:
        raise HTTPException(status_code=400, detail="CSV must have an 'email' column header.")

    # Normalise field names to lowercase
    def field(row: dict, name: str) -> str:
        for k, v in row.items():
            if k.strip().lower() == name:
                return (v or "").strip()
        return ""

    added      = 0
    duplicates: list[ImportRow] = []
    errors:     list[ImportRow] = []

    from ..utils.security import hash_password as _hash

    for row_num, row in enumerate(reader, start=2):   # row 1 = header
        email    = field(row, "email").lower()
        plate    = field(row, "plate").upper() or None
        password = field(row, "password") or "Temp123!"

        if not email:
            errors.append(ImportRow(row=row_num, email=email, plate=plate,
                                    reason="Email is required"))
            continue

        # Duplicate email check
        if db.query(User).filter(User.email == email).first():
            duplicates.append(ImportRow(row=row_num, email=email, plate=plate,
                                        reason="Email already exists"))
            continue

        # Duplicate plate check
        if plate and db.query(RegisteredVehicle).filter(
            RegisteredVehicle.plate == plate
        ).first():
            duplicates.append(ImportRow(row=row_num, email=email, plate=plate,
                                        reason="Plate already registered"))
            continue

        try:
            new_user = User(
                email=email,
                password_hash=_hash(password),
                role=UserRole.PARKER,
            )
            db.add(new_user)
            db.flush()

            # Create token balance
            db.add(TokenBalance(user_id=new_user.id, balance=0))

            # Register vehicle if provided
            if plate:
                db.add(RegisteredVehicle(user_id=new_user.id, plate=plate))

            db.commit()
            added += 1
        except Exception as exc:
            db.rollback()
            errors.append(ImportRow(row=row_num, email=email, plate=plate,
                                    reason=f"Database error: {exc}"))

    return ImportResult(added=added, duplicates=duplicates, errors=errors)
