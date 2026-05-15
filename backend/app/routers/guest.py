from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enforcement import Citation
from ..models.guest import GuestProfile
from ..models.user import User
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/guest", tags=["guest"])


def _require_guest(current_user: User = Depends(get_current_user)) -> User:
    from ..models.user import UserRole
    if current_user.role != UserRole.GUEST:
        raise HTTPException(status_code=403, detail="Guest access only.")
    return current_user


@router.get("/profile")
def get_profile(
    current_user: User = Depends(_require_guest),
    db: Session = Depends(get_db),
):
    profile = db.query(GuestProfile).filter(GuestProfile.user_id == current_user.id).first()
    return {
        "user_id":      current_user.id,
        "email":        current_user.email,
        "name":         profile.name          if profile else current_user.name,
        "license_plate": profile.license_plate if profile else None,
        "expires_at":   profile.expires_at.isoformat() if profile else None,
        "limited_access": profile.limited_access if profile else True,
    }


@router.get("/citations")
def get_guest_citations(
    current_user: User = Depends(_require_guest),
    db: Session = Depends(get_db),
):
    """Return citations linked to this guest by user_id or by their registered plate."""
    profile = db.query(GuestProfile).filter(GuestProfile.user_id == current_user.id).first()
    plate = profile.license_plate if profile else None

    q = db.query(Citation)
    if plate:
        q = q.filter(
            (Citation.user_id == current_user.id) | (Citation.vehicle_plate == plate)
        )
    else:
        q = q.filter(Citation.user_id == current_user.id)

    citations = q.order_by(Citation.issued_at.desc()).all()
    return [
        {
            "id":             c.id,
            "plate":          c.vehicle_plate,
            "zone":           c.zone,
            "violation_type": c.violation_type,
            "fine_amount":    c.fine_amount,
            "issued_at":      c.issued_at.isoformat(),
            "paid":           c.paid,
            "appealed":       c.appealed,
        }
        for c in citations
    ]


@router.post("/citations/{citation_id}/appeal")
def appeal_citation(
    citation_id: int,
    current_user: User = Depends(_require_guest),
    db: Session = Depends(get_db),
):
    profile = db.query(GuestProfile).filter(GuestProfile.user_id == current_user.id).first()
    plate   = profile.license_plate if profile else None

    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise HTTPException(status_code=404, detail="Citation not found.")

    # Only allow appeal if citation belongs to this guest
    if citation.user_id != current_user.id and (not plate or citation.vehicle_plate != plate):
        raise HTTPException(status_code=403, detail="Not authorized to appeal this citation.")

    if citation.appealed:
        raise HTTPException(status_code=400, detail="Citation has already been appealed.")

    citation.appealed = True
    db.commit()
    return {"success": True}
