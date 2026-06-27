from datetime import datetime, timezone, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.enforcement import EnforcementCheck, Citation
from ..models.parking import ParkingSession, HistoricParkingSession


def get_chart_data(db: Session) -> dict:
    today = datetime.now(timezone.utc).date()
    thirty_ago = today - timedelta(days=29)

    live_by_day = (
        db.query(func.date(ParkingSession.started_at).label("d"), func.count().label("n"))
        .filter(func.date(ParkingSession.started_at) >= thirty_ago)
        .group_by(func.date(ParkingSession.started_at))
        .all()
    )

    hist_by_day = (
        db.query(func.date(HistoricParkingSession.started_at).label("d"), func.count().label("n"))
        .filter(func.date(HistoricParkingSession.started_at) >= thirty_ago)
        .group_by(func.date(HistoricParkingSession.started_at))
        .all()
    )

    live_by_zone = (
        db.query(ParkingSession.zone, func.count().label("n"))
        .group_by(ParkingSession.zone)
        .all()
    )

    user_type_dist = (
        db.query(HistoricParkingSession.user_type, func.count().label("n"))
        .group_by(HistoricParkingSession.user_type)
        .all()
    )

    payment_dist = (
        db.query(HistoricParkingSession.payment_type, func.count().label("n"))
        .group_by(HistoricParkingSession.payment_type)
        .all()
    )

    enforcement_dist = (
        db.query(HistoricParkingSession.enforcement_status, func.count().label("n"))
        .group_by(HistoricParkingSession.enforcement_status)
        .all()
    )

    session_type_dist = (
        db.query(HistoricParkingSession.session_type, func.count().label("n"))
        .group_by(HistoricParkingSession.session_type)
        .all()
    )

    return {
        "sessions_per_day": {
            "live": [{"date": str(r.d), "count": r.n} for r in live_by_day],
            "historic": [{"date": str(r.d), "count": r.n} for r in hist_by_day],
        },
        "sessions_by_zone": [{"zone": r.zone, "count": r.n} for r in live_by_zone],
        "user_type_distribution": [{"type": r.user_type, "count": r.n} for r in user_type_dist],
        "payment_distribution": [{"type": r.payment_type, "count": r.n} for r in payment_dist],
        "enforcement_distribution": [{"status": r.enforcement_status, "count": r.n} for r in enforcement_dist],
        "session_type_distribution": [{"type": r.session_type, "count": r.n} for r in session_type_dist],
    }
