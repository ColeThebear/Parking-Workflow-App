from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models.user import User, UserRole

settings = get_settings()

# HTTPBearer handles Authorization header parsing and adds the security scheme
# to the OpenAPI docs. auto_error=False lets us return a proper 401 instead
# of FastAPI's default 403 when no credentials are provided.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer token and return the authenticated User."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _require_role(role: UserRole):
    """
    Dependency factory — returns a FastAPI dependency that enforces a role.

    Each call produces a distinct closure with a unique __name__ so FastAPI's
    dependency graph caches them independently (by object identity).

        require_enforcement = _require_role(UserRole.ENFORCEMENT)
        require_operator    = _require_role(UserRole.OPERATOR)

    Usage in a route:
        current_user: User = Depends(require_enforcement)
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Requires {role.value} role",
            )
        return current_user

    _check.__name__ = f"require_{role.value.lower()}"
    return _check


require_enforcement = _require_role(UserRole.ENFORCEMENT)
require_operator    = _require_role(UserRole.OPERATOR)
require_admin       = _require_role(UserRole.ADMIN)
