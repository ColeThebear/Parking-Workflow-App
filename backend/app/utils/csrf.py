import secrets

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ..config import get_settings

_settings = get_settings()
_SECURE_COOKIE = _settings.ENVIRONMENT != "development"

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "x-csrf-token"

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# These endpoints either pre-date a session (login/register) or use token
# credentials the attacker cannot forge (refresh uses an HttpOnly cookie that
# JS can never read, so a CSRF attack cannot replay it).
_CSRF_EXEMPT = frozenset({
    "/v1/auth/login",
    "/v1/auth/register",
    "/v1/auth/guest-register",
    "/v1/auth/refresh",
})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    Only applies to cookie-authenticated (browser) requests.  API clients
    and tests that carry ``Authorization: Bearer …`` are exempt because
    bearer-token auth is not susceptible to CSRF — the token is never sent
    automatically by the browser.

    Flow
    ----
    1. On any response, the middleware writes a non-HttpOnly ``csrf_token``
       cookie if the client does not already have one.
    2. JS reads that cookie and echoes it as the ``X-CSRF-Token`` request
       header on every state-changing (non-GET) request.
    3. The middleware compares cookie == header; mismatches → 403.
    """

    async def dispatch(self, request: Request, call_next):
        if (
            request.method not in _SAFE_METHODS
            and request.url.path not in _CSRF_EXEMPT
        ):
            auth = request.headers.get("authorization", "")
            if not auth.startswith("Bearer "):
                cookie = request.cookies.get(CSRF_COOKIE, "")
                header = request.headers.get(CSRF_HEADER, "")
                if not cookie or not header or not secrets.compare_digest(cookie, header):
                    return JSONResponse(
                        {"detail": "CSRF validation failed"},
                        status_code=403,
                    )

        response = await call_next(request)

        # Issue the token cookie on every response so new browser sessions get
        # one automatically without needing a dedicated preflight call.
        if CSRF_COOKIE not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE,
                secrets.token_urlsafe(32),
                httponly=False,
                secure=_SECURE_COOKIE,
                samesite="lax",
                max_age=86400,
                path="/",
            )

        return response
