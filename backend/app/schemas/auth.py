import re

from pydantic import BaseModel, Field, field_validator


def validate_password_strength(password: str) -> str:
    """Shared password strength check — min 8 chars, upper + lower + digit."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    return password


class LoginRequest(BaseModel):
    # Both fields accepted for backward compatibility with existing tests.
    # Frontend always sends `email`.
    email:    str | None = None
    username: str | None = None
    password: str = Field(min_length=1)


class Token(BaseModel):
    """Kept for internal use and programmatic API clients only.
    The browser-facing login flow uses AuthSuccess — no tokens in the body."""
    access_token:           str
    refresh_token:          str | None = None
    token_type:             str  = "bearer"
    role:                   str | None = None
    terminated_by_operator: bool = False
    admin_permission:        str | None = None


class AuthSuccess(BaseModel):
    """Response body for cookie-based auth endpoints.
    Tokens are delivered as HttpOnly cookies, not in this payload."""
    role:                   str
    admin_permission:       str | None = None
    terminated_by_operator: bool = False


class RefreshRequest(BaseModel):
    """Legacy: accepts refresh_token in body for programmatic/API clients.
    The browser path reads from the refresh_token HttpOnly cookie instead."""
    refresh_token: str | None = None


class GuestRegisterRequest(BaseModel):
    name:          str   = Field(min_length=1, max_length=120)
    email:         str   = Field(min_length=3)
    password:      str   = Field(min_length=8)
    license_plate: str | None = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


class AdminResetPasswordRequest(BaseModel):
    user_id: int


class AdminResetPasswordResponse(BaseModel):
    user_id:        int
    email:          str
    temp_password:  str
