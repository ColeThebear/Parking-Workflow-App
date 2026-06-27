import csv
import io
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.parking import HistoricParkingSession
from ..models.token import TokenBalance
from ..models.user import User, UserRole
from ..models.vehicle import RegisteredVehicle
from ..schemas.parking import HistoricImportRow, HistoricImportResult
from ..utils.security import hash_password

VALID_USER_TYPES = {"STUDENT", "GUEST", "UNREGISTERED"}
VALID_SESSION_TYPES = {"STANDARD", "PERMIT", "EVENT"}
VALID_PAYMENT_TYPES = {"TOKEN", "CASH", "CARD", "FREE"}
VALID_ENFORCEMENT_STATS = {"NONE", "CHECKED", "CITED"}


def _field(row: dict, name: str) -> str:
    for k, v in row.items():
        if k.strip().lower() == name:
            return (v or "").strip()
    return ""


def _parse_dt(raw: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class ImportRow:
    def __init__(self, row: int, email: str, plate: Optional[str], reason: str):
        self.row = row
        self.email = email
        self.plate = plate
        self.reason = reason


class ImportResult:
    def __init__(self, added: int, duplicates: list, errors: list):
        self.added = added
        self.duplicates = duplicates
        self.errors = errors


def import_students(db: Session, csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None or "email" not in [f.lower() for f in reader.fieldnames]:
        raise ValueError("CSV must have an 'email' column header.")

    added = 0
    duplicates: list[dict] = []
    errors: list[dict] = []

    for row_num, row in enumerate(reader, start=2):
        email = _field(row, "email").lower()
        plate = _field(row, "plate").upper() or None
        password = _field(row, "password") or "Temp123!"

        if not email:
            errors.append({"row": row_num, "email": email, "plate": plate, "reason": "Email is required"})
            continue

        if db.query(User).filter(User.email == email).first():
            duplicates.append({"row": row_num, "email": email, "plate": plate, "reason": "Email already exists"})
            continue

        if plate and db.query(RegisteredVehicle).filter(RegisteredVehicle.plate == plate).first():
            duplicates.append({"row": row_num, "email": email, "plate": plate, "reason": "Plate already registered"})
            continue

        try:
            new_user = User(email=email, password_hash=hash_password(password), role=UserRole.PARKER)
            db.add(new_user)
            db.flush()
            db.add(TokenBalance(user_id=new_user.id, balance=0))
            if plate:
                db.add(RegisteredVehicle(user_id=new_user.id, plate=plate))
            db.commit()
            added += 1
        except Exception as exc:
            db.rollback()
            errors.append({"row": row_num, "email": email, "plate": plate, "reason": f"Database error: {exc}"})

    return {"added": added, "duplicates": duplicates, "errors": errors}


def import_historic_sessions(db: Session, csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no headers.")

    lower_fields = [f.strip().lower() for f in reader.fieldnames]
    for required in ("plate", "zone", "started_at"):
        if required not in lower_fields:
            raise ValueError(f"CSV must have a '{required}' column.")

    added = 0
    duplicates: list[dict] = []
    errors: list[dict] = []

    for row_num, row in enumerate(reader, start=2):
        plate = _field(row, "plate").upper()
        zone = _field(row, "zone").strip().title()
        started_raw = _field(row, "started_at")

        if not plate:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw, "reason": "plate is required"})
            continue
        if not zone:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw, "reason": "zone is required"})
            continue
        if not started_raw:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw, "reason": "started_at is required"})
            continue

        started_at = _parse_dt(started_raw)
        if not started_at:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": "started_at must be YYYY-MM-DD HH:MM"})
            continue

        ended_raw = _field(row, "ended_at")
        ended_at = _parse_dt(ended_raw) if ended_raw else None

        duration_minutes: Optional[int] = None
        if started_at and ended_at:
            duration_minutes = max(0, int((ended_at - started_at).total_seconds() / 60))

        raw_user_type = _field(row, "user_type").upper() or "STUDENT"
        raw_sess_type = _field(row, "session_type").upper() or "STANDARD"
        raw_pay_type = _field(row, "payment_type").upper() or "FREE"
        raw_enf_status = _field(row, "enforcement_status").upper() or "NONE"

        if raw_user_type not in VALID_USER_TYPES:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": f"user_type '{raw_user_type}' invalid. Use: {', '.join(VALID_USER_TYPES)}"})
            continue
        if raw_sess_type not in VALID_SESSION_TYPES:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": f"session_type '{raw_sess_type}' invalid. Use: {', '.join(VALID_SESSION_TYPES)}"})
            continue
        if raw_pay_type not in VALID_PAYMENT_TYPES:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": f"payment_type '{raw_pay_type}' invalid. Use: {', '.join(VALID_PAYMENT_TYPES)}"})
            continue
        if raw_enf_status not in VALID_ENFORCEMENT_STATS:
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": f"enforcement_status '{raw_enf_status}' invalid. Use: {', '.join(VALID_ENFORCEMENT_STATS)}"})
            continue

        existing = db.query(HistoricParkingSession).filter(
            HistoricParkingSession.vehicle_plate == plate,
            HistoricParkingSession.started_at == started_at,
        ).first()
        if existing:
            duplicates.append({"row": row_num, "plate": plate, "started_at": started_raw,
                               "reason": "Duplicate: same plate and start time already imported"})
            continue

        try:
            db.add(HistoricParkingSession(
                vehicle_plate=plate, zone=zone, started_at=started_at,
                ended_at=ended_at, duration_minutes=duration_minutes,
                user_type=raw_user_type, session_type=raw_sess_type,
                payment_type=raw_pay_type, enforcement_status=raw_enf_status,
                notes=_field(row, "notes") or None,
            ))
            db.commit()
            added += 1
        except Exception as exc:
            db.rollback()
            errors.append({"row": row_num, "plate": plate, "started_at": started_raw,
                           "reason": f"Database error: {exc}"})

    return {"added": added, "duplicates": duplicates, "errors": errors}
