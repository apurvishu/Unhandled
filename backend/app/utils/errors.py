"""
Standardized error handling for the application.
"""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(HTTPException):
    """
    Custom application exception with structured error response.

    Usage:
        raise AppException(
            status_code=404,
            error_code="VESSEL_NOT_FOUND",
            message="Vessel does not exist.",
        )
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ):
        detail = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
            },
        }
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# ===== Pre-defined exceptions =====

class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: Any = None):
        msg = f"{resource} not found." if resource_id is None else f"{resource} with ID {resource_id} not found."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=f"{resource.upper().replace(' ', '_')}_NOT_FOUND",
            message=msg,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            message=message,
        )


class ConflictException(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message=message,
        )


class BadRequestException(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            message=message,
        )


class RateLimitException(AppException):
    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message=message,
        )


# ===== Exception handlers =====

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with structured response."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": errors,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTPException and format nicely."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    elif isinstance(exc.detail, dict):
        content = {"success": False, "error": exc.detail}
    else:
        # Default error code based on status code
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_ERROR",
        }
        code = error_codes.get(exc.status_code, "ERROR")
        content = {
            "success": False,
            "error": {
                "code": code,
                "message": str(exc.detail),
            },
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )
