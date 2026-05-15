from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, UserRole
from ..models.guest import GuestProfile
from ..schemas.auth import LoginRequest, Token, GuestRegisterRequest
from ..utils.security import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = (payload.email or payload.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username required")

    user = db.query(User).filter(User.email == identifier).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Guest expiry check — expired guest accounts cannot log in.
    if user.role == UserRole.GUEST:
        profile = db.query(GuestProfile).filter(GuestProfile.user_id == user.id).first()
        if profile and profile.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=403,
                detail="Your guest account has expired. Please contact the parking office.",
            )

    # Read and atomically reset the termination flag so it only shows once.
    was_terminated = bool(user.terminated_by_operator)
    if was_terminated:
        user.terminated_by_operator = False
        db.commit()

    token = create_token({"sub": str(user.id), "role": user.role.value})
    return Token(
        access_token=token,
        role=user.role.value,
        terminated_by_operator=was_terminated,
        admin_permission=user.admin_permission,
    )


@router.post("/register", response_model=Token)
def register(payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = (payload.email or payload.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username required")

    if db.query(User).filter(User.email == identifier).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=identifier,
        password_hash=hash_password(payload.password),
        role=UserRole.PARKER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, role=user.role.value)


@router.post("/guest-register", response_model=Token)
def guest_register(payload: GuestRegisterRequest, db: Session = Depends(get_db)):
    """
    Self-registration endpoint for guest (walk-up) users.
    Creates a User (role=GUEST) + GuestProfile with academic-year expiry.
    """
    email = payload.email.strip().lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="An account with that email already exists.")

    plate = payload.license_plate.strip().upper() if payload.license_plate else None

    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.GUEST,
    )
    db.add(user)
    db.flush()  # get user.id

    profile = GuestProfile(
        user_id=user.id,
        name=payload.name.strip(),
        license_plate=plate,
        limited_access=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    token = create_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, role=user.role.value)
