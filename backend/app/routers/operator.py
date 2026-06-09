import csv
import io
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.enforcement import EnforcementCheck, Citation
from ..models.parking import ParkingSession, HistoricParkingSession
from ..models.token import TokenBalance
from ..models.user import User, UserRole
from ..models.vehicle import RegisteredVehicle
from ..schemas.parking import (
    ParkingSessionOut,
    StudentSearchResult,
    EndSessionRequest,
    EndSessionResponse,
    HistoricSessionOut,
    HistoricImportRow,
    HistoricImportResult,
)
from ..utils.dependencies import require_operator
from ..utils.security import hash_password

VALID_USER_TYPES        = {"STUDENT", "GUEST", "UNREGISTERED"}
VALID_SESSION_TYPES     = {"STANDARD", "PERMIT", "EVENT"}
VALID_PAYMENT_TYPES     = {"TOKEN", "CASH", "CARD", "FREE"}
VALID_ENFORCEMENT_STATS = {"NONE", "CHECKED", "CITED"}

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


# ── Historic sessions ─────────────────────────────────────────────────────────

@router.get("/historic-sessions", response_model=list[HistoricSessionOut])
def get_historic_sessions(
    date_from:          Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to:            Optional[str] = Query(None, description="YYYY-MM-DD"),
    plate:              Optional[str] = Query(None),
    user_type:          Optional[str] = Query(None),
    zone:               Optional[str] = Query(None),
    session_type:       Optional[str] = Query(None),
    payment_type:       Optional[str] = Query(None),
    enforcement_status: Optional[str] = Query(None),
    duration_min:       Optional[int] = Query(None, ge=0),
    duration_max:       Optional[int] = Query(None, ge=0),
    limit:              int           = Query(200, ge=1, le=1000),
    offset:             int           = Query(0, ge=0),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    q = db.query(HistoricParkingSession)

    if date_from:
        try:
            q = q.filter(HistoricParkingSession.started_at >= datetime.fromisoformat(date_from))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from must be YYYY-MM-DD")
    if date_to:
        try:
            end = datetime.fromisoformat(date_to) + timedelta(days=1)
            q = q.filter(HistoricParkingSession.started_at < end)
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to must be YYYY-MM-DD")
    if plate:
        q = q.filter(HistoricParkingSession.vehicle_plate.ilike(f"%{plate.upper()}%"))
    if user_type:
        q = q.filter(HistoricParkingSession.user_type == user_type.upper())
    if zone:
        q = q.filter(HistoricParkingSession.zone == zone)
    if session_type:
        q = q.filter(HistoricParkingSession.session_type == session_type.upper())
    if payment_type:
        q = q.filter(HistoricParkingSession.payment_type == payment_type.upper())
    if enforcement_status:
        q = q.filter(HistoricParkingSession.enforcement_status == enforcement_status.upper())
    if duration_min is not None:
        q = q.filter(HistoricParkingSession.duration_minutes >= duration_min)
    if duration_max is not None:
        q = q.filter(HistoricParkingSession.duration_minutes <= duration_max)

    total = q.count()
    rows = q.order_by(HistoricParkingSession.started_at.desc()).offset(offset).limit(limit).all()
    return rows


# ── Historic CSV import ───────────────────────────────────────────────────────

@router.post("/import-historic", response_model=HistoricImportResult)
async def import_historic_sessions(
    file: UploadFile = File(...),
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """
    Import historic parking session data from CSV.

    Required columns: plate, zone, started_at (YYYY-MM-DD HH:MM or ISO)
    Optional columns: ended_at, user_type, session_type, payment_type,
                      enforcement_status, notes

    Duplicate detection: same plate + started_at is skipped.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV has no headers.")

    lower_fields = [f.strip().lower() for f in reader.fieldnames]
    for required in ("plate", "zone", "started_at"):
        if required not in lower_fields:
            raise HTTPException(
                status_code=400, detail=f"CSV must have a '{required}' column."
            )

    def field(row: dict, name: str) -> str:
        for k, v in row.items():
            if k.strip().lower() == name:
                return (v or "").strip()
        return ""

    def parse_dt(raw: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    added      = 0
    duplicates: list[HistoricImportRow] = []
    errors:     list[HistoricImportRow] = []

    for row_num, row in enumerate(reader, start=2):
        plate      = field(row, "plate").upper()
        zone       = field(row, "zone")
        started_raw = field(row, "started_at")

        if not plate:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw, reason="plate is required"))
            continue
        if not zone:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw, reason="zone is required"))
            continue
        if not started_raw:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw, reason="started_at is required"))
            continue

        started_at = parse_dt(started_raw)
        if not started_at:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason="started_at must be YYYY-MM-DD HH:MM"))
            continue

        ended_raw = field(row, "ended_at")
        ended_at  = parse_dt(ended_raw) if ended_raw else None

        duration_minutes: Optional[int] = None
        if started_at and ended_at:
            duration_minutes = max(0, int((ended_at - started_at).total_seconds() / 60))

        raw_user_type  = field(row, "user_type").upper()  or "STUDENT"
        raw_sess_type  = field(row, "session_type").upper() or "STANDARD"
        raw_pay_type   = field(row, "payment_type").upper() or "FREE"
        raw_enf_status = field(row, "enforcement_status").upper() or "NONE"

        if raw_user_type not in VALID_USER_TYPES:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason=f"user_type '{raw_user_type}' invalid. Use: {', '.join(VALID_USER_TYPES)}"))
            continue
        if raw_sess_type not in VALID_SESSION_TYPES:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason=f"session_type '{raw_sess_type}' invalid. Use: {', '.join(VALID_SESSION_TYPES)}"))
            continue
        if raw_pay_type not in VALID_PAYMENT_TYPES:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason=f"payment_type '{raw_pay_type}' invalid. Use: {', '.join(VALID_PAYMENT_TYPES)}"))
            continue
        if raw_enf_status not in VALID_ENFORCEMENT_STATS:
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason=f"enforcement_status '{raw_enf_status}' invalid. Use: {', '.join(VALID_ENFORCEMENT_STATS)}"))
            continue

        # Duplicate check: same plate + started_at
        existing = db.query(HistoricParkingSession).filter(
            HistoricParkingSession.vehicle_plate == plate,
            HistoricParkingSession.started_at    == started_at,
        ).first()
        if existing:
            duplicates.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                                reason="Duplicate: same plate and start time already imported"))
            continue

        try:
            db.add(HistoricParkingSession(
                vehicle_plate      = plate,
                zone               = zone,
                started_at         = started_at,
                ended_at           = ended_at,
                duration_minutes   = duration_minutes,
                user_type          = raw_user_type,
                session_type       = raw_sess_type,
                payment_type       = raw_pay_type,
                enforcement_status = raw_enf_status,
                notes              = field(row, "notes") or None,
            ))
            db.commit()
            added += 1
        except Exception as exc:
            db.rollback()
            errors.append(HistoricImportRow(row=row_num, plate=plate, started_at=started_raw,
                                            reason=f"Database error: {exc}"))

    return HistoricImportResult(added=added, duplicates=duplicates, errors=errors)


# ── Chart data ────────────────────────────────────────────────────────────────

@router.get("/chart-data")
def get_chart_data(
    _: User = Depends(require_operator),
    db: Session = Depends(get_db),
):
    """Aggregated data for Plotly charts on the operator dashboard."""
    today        = datetime.now(timezone.utc).date()
    thirty_ago   = today - timedelta(days=29)

    # Sessions per day — live table (last 30 days)
    live_by_day = (
        db.query(func.date(ParkingSession.started_at).label("d"), func.count().label("n"))
        .filter(func.date(ParkingSession.started_at) >= thirty_ago)
        .group_by(func.date(ParkingSession.started_at))
        .all()
    )

    # Sessions per day — historic table (last 30 days)
    hist_by_day = (
        db.query(func.date(HistoricParkingSession.started_at).label("d"), func.count().label("n"))
        .filter(func.date(HistoricParkingSession.started_at) >= thirty_ago)
        .group_by(func.date(HistoricParkingSession.started_at))
        .all()
    )

    # Sessions by zone — live (all time)
    live_by_zone = (
        db.query(ParkingSession.zone, func.count().label("n"))
        .group_by(ParkingSession.zone)
        .all()
    )

    # Historic: user_type distribution
    user_type_dist = (
        db.query(HistoricParkingSession.user_type, func.count().label("n"))
        .group_by(HistoricParkingSession.user_type)
        .all()
    )

    # Historic: payment_type distribution
    payment_dist = (
        db.query(HistoricParkingSession.payment_type, func.count().label("n"))
        .group_by(HistoricParkingSession.payment_type)
        .all()
    )

    # Historic: enforcement_status distribution
    enforcement_dist = (
        db.query(HistoricParkingSession.enforcement_status, func.count().label("n"))
        .group_by(HistoricParkingSession.enforcement_status)
        .all()
    )

    # Historic: session_type distribution
    session_type_dist = (
        db.query(HistoricParkingSession.session_type, func.count().label("n"))
        .group_by(HistoricParkingSession.session_type)
        .all()
    )

    return {
        "sessions_per_day": {
            "live":     [{"date": str(r.d), "count": r.n} for r in live_by_day],
            "historic": [{"date": str(r.d), "count": r.n} for r in hist_by_day],
        },
        "sessions_by_zone":       [{"zone": r.zone, "count": r.n} for r in live_by_zone],
        "user_type_distribution":  [{"type": r.user_type, "count": r.n} for r in user_type_dist],
        "payment_distribution":    [{"type": r.payment_type, "count": r.n} for r in payment_dist],
        "enforcement_distribution":[{"status": r.enforcement_status, "count": r.n} for r in enforcement_dist],
        "session_type_distribution":[{"type": r.session_type, "count": r.n} for r in session_type_dist],
    }
