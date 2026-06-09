from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ParkingStart(BaseModel):
    """
    Input schema for POST /student/start.
    Frontend sends { plate, zone } — field name matches the frontend.
    The route handler maps plate → vehicle_plate on the ORM object.
    """
    plate: str
    zone: str


class ParkingSessionOut(BaseModel):
    """
    Output schema for all session responses.

    Uses validation_alias to read from ORM column names (vehicle_plate,
    started_at, id) and outputs frontend-friendly names (plate, start_time,
    session_id) — without requiring any changes to the DB schema.
    """
    model_config = ConfigDict(
        from_attributes=True,   # Read from SQLAlchemy ORM objects
        populate_by_name=True,  # Allow both field name and alias during validation
    )

    session_id: int            = Field(validation_alias="id")
    plate:      str            = Field(validation_alias="vehicle_plate")
    zone:       str
    start_time: datetime       = Field(validation_alias="started_at")
    expires_at: datetime | None = None
    user_name:  str | None     = None   # Populated explicitly by enforcement route if needed


class LookupResponse(BaseModel):
    """
    Wrapper returned by GET /enforcement/lookup.
    success=False at HTTP 200 means "not parked" (not an error).
    success=True means an active session was found.
    """
    success: bool
    data:    Optional[ParkingSessionOut] = None


# ── Operator schemas ──────────────────────────────────────────────────────────

class StudentSearchResult(BaseModel):
    """One student record returned by GET /operator/search."""
    user_id:        int
    email:          str
    active_session: Optional[ParkingSessionOut] = None
    recent_sessions: list[ParkingSessionOut]    = []


class EndSessionRequest(BaseModel):
    session_id: int


class EndSessionResponse(BaseModel):
    success: bool
    message: str


# ── Historic session schemas ──────────────────────────────────────────────────

class HistoricSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                 int
    vehicle_plate:      str
    zone:               str
    started_at:         datetime
    ended_at:           Optional[datetime] = None
    duration_minutes:   Optional[int]      = None
    user_type:          str
    session_type:       str
    payment_type:       str
    enforcement_status: str
    notes:              Optional[str]      = None
    imported_at:        datetime


class HistoricImportRow(BaseModel):
    row:       int
    plate:     str
    started_at: str
    reason:    str


class HistoricImportResult(BaseModel):
    added:      int
    duplicates: list[HistoricImportRow]
    errors:     list[HistoricImportRow]
