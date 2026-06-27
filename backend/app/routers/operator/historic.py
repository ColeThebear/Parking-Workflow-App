from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...models.parking import HistoricParkingSession
from ...models.user import User
from ...schemas.parking import HistoricSessionOut
from ...utils.dependencies import require_operator

router = APIRouter()


@router.get("/historic-sessions", response_model=list[HistoricSessionOut])
def get_historic_sessions(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    plate: Optional[str] = Query(None),
    user_type: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    session_type: Optional[str] = Query(None),
    payment_type: Optional[str] = Query(None),
    enforcement_status: Optional[str] = Query(None),
    duration_min: Optional[int] = Query(None, ge=0),
    duration_max: Optional[int] = Query(None, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
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

    return q.order_by(HistoricParkingSession.started_at.desc()).offset(offset).limit(limit).all()
