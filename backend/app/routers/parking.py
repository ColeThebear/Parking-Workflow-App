from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.parking import ParkingSession
from ..schemas.parking import ParkingStart, ParkingSessionOut

router = APIRouter(prefix="/parking", tags=["parking"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/start", response_model=ParkingSessionOut)
def start_parking(payload: ParkingStart, db: Session = Depends(get_db)):
    session = ParkingSession(
        vehicle_plate=payload.vehicle_plate,
        zone=payload.zone,
        user_id=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/plate/{plate}", response_model=list[ParkingSessionOut])
def get_by_plate(plate: str, db: Session = Depends(get_db)):
    sessions = (
        db.query(ParkingSession)
        .filter(ParkingSession.vehicle_plate == plate)
        .order_by(ParkingSession.started_at.desc())
        .all()
    )
    return sessions