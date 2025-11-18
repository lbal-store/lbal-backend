from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    RATE_LIMITED = "RATE_LIMITED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ACCESS_DENIED = "ACCESS_DENIED"
    HTTP_ERROR = "HTTP_ERROR"


class ApplicationError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode | str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code.value if isinstance(code, ErrorCode) else str(code)
        self.message = message
        self.status_code = status_code
        self.details = details


def error_content(code: ErrorCode | str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code.value if isinstance(code, ErrorCode) else str(code), "message": message}
    if details:
        payload["details"] = details
    return {"error": payload}


def setup_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = _format_validation_errors(exc)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_content(ErrorCode.VALIDATION_ERROR, "Invalid request body.", details),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        code = ErrorCode.UNAUTHORIZED if exc.status_code == status.HTTP_401_UNAUTHORIZED else ErrorCode.HTTP_ERROR
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=error_content(code, message),
        )


def _format_validation_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []) if isinstance(part, (str, int)))
        if not field:
            field = "non_field_error"
        errors[field] = error.get("msg", "Invalid value")
    return errors
