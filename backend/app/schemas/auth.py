from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Both fields accepted for backward compatibility with existing tests.
    # Frontend always sends `email`.
    email:    str | None = None
    username: str | None = None
    password: str = Field(min_length=1)


class Token(BaseModel):
    access_token:           str
    token_type:             str  = "bearer"
    role:                   str | None = None
    # True when the student's last session was ended by an operator.
    # The login endpoint resets this flag to False after reading it.
    terminated_by_operator: bool = False
    # ADMIN users only: full_admin | events_admin | citations_admin | reporting_admin
    admin_permission:        str | None = None


class GuestRegisterRequest(BaseModel):
    name:          str   = Field(min_length=1, max_length=120)
    email:         str   = Field(min_length=3)
    password:      str   = Field(min_length=6)
    license_plate: str | None = None
