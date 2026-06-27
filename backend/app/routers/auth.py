import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.user import User, UserRole
from ..models.guest import GuestProfile
from ..schemas.auth import (
    LoginRequest, Token, GuestRegisterRequest,
    ChangePasswordRequest, RefreshRequest, validate_password_strength,
)
from ..utils.security import hash_password, verify_password, create_token, create_refresh_token
from ..utils.dependencies import get_current_user
from ..utils.rate_limit import limiter

logger = logging.getLogger("api.auth")
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User, **extra_fields) -> Token:
    payload = {"sub": str(user.id), "role": user.role.value}
    return Token(
        access_token=create_token(payload),
        refresh_token=create_refresh_token(payload),
        role=user.role.value,
        admin_permission=user.admin_permission,
        **extra_fields,
    )


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = (payload.email or payload.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username required")

    user = db.query(User).filter(User.email == identifier).first()

    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("Login failed for %s", identifier)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role == UserRole.GUEST:
        profile = db.query(GuestProfile).filter(GuestProfile.user_id == user.id).first()
        if profile and profile.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=403,
                detail="Your guest account has expired. Please contact the parking office.",
            )

    was_terminated = bool(user.terminated_by_operator)
    if was_terminated:
        user.terminated_by_operator = False
        db.commit()

    logger.info("Login success user_id=%d role=%s", user.id, user.role.value)
    return _issue_tokens(user, terminated_by_operator=was_terminated)


@router.post("/register", response_model=Token)
@limiter.limit("3/minute")
def register(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    identifier = (payload.email or payload.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username required")

    try:
        validate_password_strength(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

    logger.info("Register success user_id=%d email=%s", user.id, user.email)
    return _issue_tokens(user)


@router.post("/guest-register", response_model=Token)
@limiter.limit("3/minute")
def guest_register(request: Request, payload: GuestRegisterRequest, db: Session = Depends(get_db)):
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
    db.flush()

    profile = GuestProfile(
        user_id=user.id,
        name=payload.name.strip(),
        license_plate=plate,
        limited_access=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    logger.info("Guest register success user_id=%d email=%s", user.id, user.email)
    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return _issue_tokens(user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    logger.info("Password changed user_id=%d", current_user.id)
    return {"success": True}
