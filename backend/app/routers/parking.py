from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.parking import ParkingSession
from ..models.user import User
from ..schemas.parking import ParkingStart, ParkingSessionOut
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/student", tags=["student"])


PARKING_SESSION_HOURS = 1


def _to_out(session: ParkingSession) -> ParkingSessionOut:
    return ParkingSessionOut(
        session_id=session.id,
        plate=session.vehicle_plate,
        zone=session.zone,
        start_time=session.started_at,
        expires_at=session.expires_at,
        user_name=None,
    )


def _active_filter(query, user_id: int):
    """Filter for sessions that are active and not yet expired.
    Rows with NULL expires_at (legacy seed data) are always excluded by active=False."""
    now = datetime.now(timezone.utc)
    return query.filter(
        ParkingSession.user_id == user_id,
        ParkingSession.active.is_(True),
        or_(ParkingSession.expires_at.is_(None), ParkingSession.expires_at > now),
    )


@router.post("/start")
def start_parking(
    payload: ParkingStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = _active_filter(db.query(ParkingSession), current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active parking session.")

    now = datetime.now(timezone.utc)
    session = ParkingSession(
        vehicle_plate=payload.plate,
        zone=payload.zone,
        user_id=current_user.id,
        started_at=now,
        expires_at=now + timedelta(hours=PARKING_SESSION_HOURS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _to_out(session)


@router.get("/active")
def get_my_active_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _active_filter(db.query(ParkingSession), current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="No active session found.")

    return {"data": _to_out(session)}


@router.post("/end")
def end_parking(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _active_filter(db.query(ParkingSession), current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="No active session found.")

    session.active = False
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return _to_out(session)


@router.get("/my-sessions")
def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ParkingSession)
        .filter(ParkingSession.user_id == current_user.id)
        .order_by(ParkingSession.started_at.desc())
        .all()
    )
    return [_to_out(s) for s in sessions]


@router.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models.token import TokenBalance, Transaction
    bal = db.query(TokenBalance).filter(TokenBalance.user_id == current_user.id).first()
    if not bal:
        # Create on first access
        bal = TokenBalance(user_id=current_user.id, balance=0)
        db.add(bal)
        db.commit()
        db.refresh(bal)
    txns = (
        db.query(Transaction)
        .filter(Transaction.balance_id == bal.id)
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "balance": bal.balance,
        "transactions": [
            {
                "amount":      t.amount,
                "description": t.description,
                "tx_type":     t.tx_type,
                "created_at":  t.created_at.isoformat(),
            }
            for t in txns
        ],
    }
