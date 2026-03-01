from pydantic import BaseModel
from datetime import datetime

class ParkingStart(BaseModel):
    vehicle_plate: str
    zone: str

class ParkingSessionOut(BaseModel):
    id: int
    vehicle_plate: str
    zone: str
    started_at: datetime
    ended_at: datetime | None
    active: bool

    class Config:
        orm_mode = True