from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.parking import ParkingSession
from ...models.user import User, UserRole
from ...schemas.parking import ParkingSessionOut, StudentSearchResult
from ...utils.dependencies import require_operator

router = APIRouter()


def _session_to_out(s: ParkingSession) -> ParkingSessionOut:
    return ParkingSessionOut(
        session_id=s.id, plate=s.vehicle_plate, zone=s.zone,
        start_time=s.started_at, expires_at=s.expires_at,
    )


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
        .filter(ParkingSession.user_id.isnot(None),
                func.lower(ParkingSession.vehicle_plate).like(term))
        .distinct().all()
        if row.user_id is not None
    }

    user_ids = list(email_ids | plate_ids)[:10]
    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    now = datetime.now(timezone.utc)

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
            user_id=user.id, email=user.email,
            active_session=_session_to_out(active) if active else None,
            recent_sessions=[_session_to_out(s) for s in sessions],
        ))
    return results
