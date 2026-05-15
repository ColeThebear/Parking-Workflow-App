from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.enforcement import EnforcementCheck, Citation
from ..models.parking import ParkingSession
from ..models.user import User
from ..schemas.parking import ParkingSessionOut, LookupResponse
from ..utils.dependencies import require_enforcement

router = APIRouter(prefix="/enforcement", tags=["enforcement"])

VIOLATION_TYPES = [
    "No Valid Session",
    "Expired Session",
    "Wrong Zone",
    "No Permit",
    "Handicap Violation",
    "Fire Lane",
    "Other",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _session_to_out(s: ParkingSession) -> ParkingSessionOut:
    return ParkingSessionOut(
        session_id=s.id,
        plate=s.vehicle_plate,
        zone=s.zone,
        start_time=s.started_at,
        expires_at=s.expires_at,
        user_name=s.user.email if s.user else None,
    )


# ── Plate Lookup (with check logging) ─────────────────────────────────────────

@router.get("/lookup", response_model=LookupResponse)
def lookup_active_parking(
    plate: str = Query(..., description="Vehicle plate number to look up"),
    current_user: User = Depends(require_enforcement),
    db: Session = Depends(get_db),
):
    """
    Check whether a vehicle is currently parked.
    Logs an EnforcementCheck record every time this is called.
    """
    normalized = plate.strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="Plate number is required.")

    now = datetime.now(timezone.utc)
    session = (
        db.query(ParkingSession)
        .filter(
            ParkingSession.vehicle_plate == normalized,
            ParkingSession.active.is_(True),
            or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now),
        )
        .first()
    )

    # Log the check
    db.add(EnforcementCheck(
        officer_id=current_user.id,
        vehicle_plate=normalized,
        session_found=session is not None,
    ))
    db.commit()

    return LookupResponse(
        success=session is not None,
        data=_session_to_out(session) if session else None,
    )


# ── Citations ─────────────────────────────────────────────────────────────────

class CitationCreate(BaseModel):
    vehicle_plate:  str
    zone:           str
    violation_type: str
    fine_amount:    int = 5000    # cents — default $50
    notes:          Optional[str] = None


class CitationOut(BaseModel):
    id:             int
    vehicle_plate:  str
    zone:           str
    violation_type: str
    fine_amount:    int
    notes:          Optional[str]
    issued_at:      datetime
    paid:           bool
    appealed:       bool
    officer_email:  str
    student_email:  Optional[str]

    class Config:
        from_attributes = True


@router.post("/citations", response_model=CitationOut)
def issue_citation(
    payload: CitationCreate,
    current_user: User = Depends(require_enforcement),
    db: Session = Depends(get_db),
):
    """Issue a parking citation for a vehicle."""
    plate = payload.vehicle_plate.strip().upper()
    if not plate:
        raise HTTPException(status_code=400, detail="Plate is required.")
    if payload.violation_type not in VIOLATION_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"Invalid violation type. Valid: {VIOLATION_TYPES}")

    # Look up the student associated with the most recent session for this plate
    now = datetime.now(timezone.utc)
    session = (
        db.query(ParkingSession)
        .filter(ParkingSession.vehicle_plate == plate)
        .order_by(ParkingSession.started_at.desc())
        .first()
    )
    user_id = session.user_id if session else None

    citation = Citation(
        officer_id=current_user.id,
        user_id=user_id,
        vehicle_plate=plate,
        zone=payload.zone,
        violation_type=payload.violation_type,
        fine_amount=payload.fine_amount,
        notes=payload.notes,
    )
    db.add(citation)
    db.commit()
    db.refresh(citation)

    return CitationOut(
        id=citation.id,
        vehicle_plate=citation.vehicle_plate,
        zone=citation.zone,
        violation_type=citation.violation_type,
        fine_amount=citation.fine_amount,
        notes=citation.notes,
        issued_at=citation.issued_at,
        paid=citation.paid,
        appealed=citation.appealed,
        officer_email=current_user.email,
        student_email=citation.student.email if citation.student else None,
    )


@router.get("/citations", response_model=list[CitationOut])
def list_my_citations(
    current_user: User = Depends(require_enforcement),
    db: Session = Depends(get_db),
):
    """All citations issued by this officer."""
    citations = (
        db.query(Citation)
        .filter(Citation.officer_id == current_user.id)
        .order_by(Citation.issued_at.desc())
        .all()
    )
    return [
        CitationOut(
            id=c.id,
            vehicle_plate=c.vehicle_plate,
            zone=c.zone,
            violation_type=c.violation_type,
            fine_amount=c.fine_amount,
            notes=c.notes,
            issued_at=c.issued_at,
            paid=c.paid,
            appealed=c.appealed,
            officer_email=c.officer.email,
            student_email=c.student.email if c.student else None,
        )
        for c in citations
    ]


@router.get("/violation-types")
def get_violation_types(_: User = Depends(require_enforcement)):
    return VIOLATION_TYPES
