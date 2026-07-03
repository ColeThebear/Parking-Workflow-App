import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.user import User, UserRole
from ..models.guest import GuestProfile
from ..models.token import RevokedToken
from ..schemas.auth import (
    LoginRequest, AuthSuccess, GuestRegisterRequest,
    ChangePasswordRequest, RefreshRequest, validate_password_strength,
    AdminResetPasswordRequest, AdminResetPasswordResponse,
)
from ..utils.security import hash_password, verify_password, create_token, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
from ..utils.dependencies import get_current_user
from ..utils.rate_limit import limiter

logger = logging.getLogger("api.auth")
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])

_SECURE_COOKIE = settings.ENVIRONMENT != "development"
_ACCESS_MAX_AGE  = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
_REFRESH_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Write both tokens as HttpOnly cookies. JS can never read these."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite="lax",
        max_age=_ACCESS_MAX_AGE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite="lax",
        max_age=_REFRESH_MAX_AGE,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _issue_auth_response(
    response: Response,
    user: User,
    **extra_fields,
) -> AuthSuccess:
    """Mint tokens, set HttpOnly cookies, return non-sensitive payload."""
    payload = {"sub": str(user.id), "role": user.role.value}
    access  = create_token(payload)
    refresh = create_refresh_token(payload)
    _set_auth_cookies(response, access, refresh)
    return AuthSuccess(
        role=user.role.value,
        admin_permission=user.admin_permission,
        **extra_fields,
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthSuccess)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
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
    return _issue_auth_response(response, user, terminated_by_operator=was_terminated)


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthSuccess)
@limiter.limit("3/minute")
def register(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    identifier = (payload.email or payload.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username required")

    try:
        validate_password_strength(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db.query(User).filter(User.email == identifier).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=identifier, password_hash=hash_password(payload.password), role=UserRole.PARKER)
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Register success user_id=%d email=%s", user.id, user.email)
    return _issue_auth_response(response, user)


# ── Guest register ────────────────────────────────────────────────────────────

@router.post("/guest-register", response_model=AuthSuccess)
@limiter.limit("3/minute")
def guest_register(
    request: Request,
    response: Response,
    payload: GuestRegisterRequest,
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="An account with that email already exists.")

    plate = payload.license_plate.strip().upper() if payload.license_plate else None
    user = User(email=email, name=payload.name.strip(),
                password_hash=hash_password(payload.password), role=UserRole.GUEST)
    db.add(user)
    db.flush()

    profile = GuestProfile(user_id=user.id, name=payload.name.strip(),
                           license_plate=plate, limited_access=True)
    db.add(profile)
    db.commit()
    db.refresh(user)

    logger.info("Guest register success user_id=%d email=%s", user.id, user.email)
    return _issue_auth_response(response, user)


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=AuthSuccess)
def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    """Issue a new access + refresh token pair.

    Token source priority:
      1. refresh_token HttpOnly cookie (browser flow)
      2. refresh_token field in the request body (programmatic / API clients)
    """
    raw = request.cookies.get("refresh_token")
    if not raw and payload:
        raw = payload.refresh_token
    if not raw:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    # Revocation check
    token_hash = _hash_token(raw)
    if db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first():
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    try:
        data = jwt.decode(raw, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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

    # Rotate: revoke the old refresh token before issuing new cookies
    expires_at = datetime.fromtimestamp(data["exp"], tz=timezone.utc)
    db.add(RevokedToken(token_hash=token_hash, expires_at=expires_at))
    db.commit()

    return _issue_auth_response(response, user)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke the refresh token and clear all auth cookies."""
    raw = request.cookies.get("refresh_token")
    if raw:
        try:
            data = jwt.decode(raw, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            expires_at = datetime.fromtimestamp(data["exp"], tz=timezone.utc)
            token_hash = _hash_token(raw)
            if not db.query(RevokedToken).filter(RevokedToken.token_hash == token_hash).first():
                db.add(RevokedToken(token_hash=token_hash, expires_at=expires_at))
                db.commit()
        except JWTError:
            pass  # Already expired — nothing to revoke

    _clear_auth_cookies(response)
    return {"success": True}


# ── Change password ───────────────────────────────────────────────────────────

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


# ── Admin password reset (kept here for colocation) ──────────────────────────

@router.post("/reset-password-admin", response_model=AdminResetPasswordResponse)
def admin_reset_password_alias(
    payload: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Thin alias — actual implementation lives in the admin router."""
    raise HTTPException(status_code=501, detail="Use /admin/reset-password")
