from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...models.enforcement import EnforcementCheck, Citation
from ...models.parking import ParkingSession
from ...models.user import User
from ...schemas.parking import ParkingSessionOut, EndSessionRequest, EndSessionResponse
from ...utils.dependencies import require_operator

router = APIRouter()


def _session_to_out(s: ParkingSession) -> ParkingSessionOut:
    return ParkingSessionOut(
        session_id=s.id, plate=s.vehicle_plate, zone=s.zone,
        start_time=s.started_at, expires_at=s.expires_at,
    )


@router.get("/stats")
def get_stats(_: User = Depends(require_operator), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    active_count = (
        db.query(func.count(ParkingSession.id))
        .filter(ParkingSession.active.is_(True),
                or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now))
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
        "active_sessions": active_count,
        "total_sessions_today": today_count,
        "enforcement_checks": check_count,
        "violations": violation_count,
    }


@router.get("/sessions/active")
def get_active_sessions(_: User = Depends(require_operator), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(ParkingSession)
        .filter(ParkingSession.active.is_(True),
                or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now))
        .order_by(ParkingSession.started_at.desc())
        .all()
    )
    return [
        {
            "session_id": s.id, "plate": s.vehicle_plate, "zone": s.zone,
            "start_time": s.started_at.isoformat() if s.started_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "student_email": s.user.email if s.user else None,
        }
        for s in sessions
    ]


@router.get("/sessions/today")
def get_todays_sessions(
    zone: Optional[str] = Query(None),
    plate: Optional[str] = Query(None),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    q = db.query(ParkingSession).filter(func.date(ParkingSession.started_at) == func.current_date())
    if zone:
        q = q.filter(ParkingSession.zone == zone)
    if plate:
        q = q.filter(ParkingSession.vehicle_plate.ilike(f"%{plate.upper()}%"))
    sessions = q.order_by(ParkingSession.started_at.desc()).all()
    return [
        {
            "session_id": s.id, "plate": s.vehicle_plate, "zone": s.zone,
            "start_time": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "active": s.active,
            "student_email": s.user.email if s.user else None,
        }
        for s in sessions
    ]


@router.get("/enforcement/checks")
def get_enforcement_checks(_: User = Depends(require_operator), db: Session = Depends(get_db)):
    checks = (
        db.query(EnforcementCheck)
        .filter(func.date(EnforcementCheck.checked_at) == func.current_date())
        .order_by(EnforcementCheck.checked_at.desc())
        .all()
    )
    return [
        {
            "id": c.id, "plate": c.vehicle_plate, "session_found": c.session_found,
            "checked_at": c.checked_at.isoformat(), "officer": c.officer.email,
        }
        for c in checks
    ]


@router.get("/enforcement/violations")
def get_violations(_: User = Depends(require_operator), db: Session = Depends(get_db)):
    citations = (
        db.query(Citation)
        .filter(func.date(Citation.issued_at) == func.current_date())
        .order_by(Citation.issued_at.desc())
        .all()
    )
    return [
        {
            "id": c.id, "plate": c.vehicle_plate, "zone": c.zone,
            "violation_type": c.violation_type, "fine_amount": c.fine_amount,
            "issued_at": c.issued_at.isoformat(), "paid": c.paid,
            "officer": c.officer.email,
            "student_email": c.student.email if c.student else None,
        }
        for c in citations
    ]


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

    session.active = False
    session.ended_at = datetime.now(timezone.utc)

    if session.user_id:
        student = db.query(User).filter(User.id == session.user_id).first()
        if student:
            student.terminated_by_operator = True

    db.commit()
    return EndSessionResponse(success=True, message="Session ended successfully.")
