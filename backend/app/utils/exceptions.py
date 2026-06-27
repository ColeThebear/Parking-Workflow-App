from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error with a structured error code."""
    def __init__(self, status_code: int, error_code: str, detail: str, field: str | None = None):
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail
        self.field = field


class DuplicateError(AppError):
    def __init__(self, detail: str, field: str | None = None):
        super().__init__(409, "DUPLICATE", detail, field)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(404, "NOT_FOUND", detail)


class ValidationError(AppError):
    def __init__(self, detail: str, field: str | None = None):
        super().__init__(400, "VALIDATION_ERROR", detail, field)


class AuthenticationError(AppError):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(401, "AUTHENTICATION_FAILED", detail)


class PermissionError(AppError):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(403, "PERMISSION_DENIED", detail)


class ExpiredError(AppError):
    def __init__(self, detail: str = "Resource has expired"):
        super().__init__(403, "EXPIRED", detail)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    body: dict = {"error_code": exc.error_code, "detail": exc.detail}
    if exc.field:
        body["field"] = exc.field
    return JSONResponse(status_code=exc.status_code, content=body)
