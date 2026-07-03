from fastapi import Depends, HTTPException, Request
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
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Validate the access token and return the authenticated User.

    Token source priority:
      1. Authorization: Bearer <token> header  (tests, programmatic API clients)
      2. access_token HttpOnly cookie          (browser / frontend)
    """
    raw_token: str | None = None
    if credentials:
        raw_token = credentials.credentials
    else:
        raw_token = request.cookies.get("access_token")

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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


def _require_admin_with_permissions(*allowed_permissions: str):
    """
    Dependency factory — enforces ADMIN role AND checks that the user's
    admin_permission is either 'full_admin' or one of the explicitly allowed
    permission strings.

        require_admin_citations = _require_admin_with_permissions("citations_admin")
        require_admin_users     = _require_admin_with_permissions("reporting_admin")
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Requires ADMIN role")
        if current_user.admin_permission == "full_admin":
            return current_user
        if current_user.admin_permission not in allowed_permissions:
            raise HTTPException(
                status_code=403,
                detail="Insufficient admin permissions",
            )
        return current_user

    names = "_".join(allowed_permissions)
    _check.__name__ = f"require_admin_{names}"
    return _check


require_admin_full      = _require_admin_with_permissions()
require_admin_citations = _require_admin_with_permissions("citations_admin")
require_admin_users     = _require_admin_with_permissions("reporting_admin")
require_admin_events    = _require_admin_with_permissions("events_admin")
