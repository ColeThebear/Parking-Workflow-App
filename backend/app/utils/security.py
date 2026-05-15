from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from ..config import get_settings

settings = get_settings()

# argon2 is used intentionally — it has no 72-byte input limit (unlike bcrypt).
# Requires: passlib[argon2] and argon2-cffi in requirements.txt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Kept as an alias — referenced by legacy seed scripts.
# Prefer hash_password() in new code.
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
