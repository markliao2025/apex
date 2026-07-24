"""Domain errors and central FastAPI exception mapping."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("apex.errors")


class AppError(Exception):
    """A safe, typed error that can be returned to an API caller."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: Any = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.retryable = retryable


def _trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", str(uuid.uuid4()))


def _response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    retryable: bool = False,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "retryable": retryable,
                "trace_id": _trace_id(request),
            }
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    """Install one response contract for domain, HTTP, validation, and 500 errors."""

    @app.middleware("http")
    async def add_trace_id(request: Request, call_next):
        request.state.trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Trace-ID"] = request.state.trace_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.info(
            "request_failed trace_id=%s code=%s path=%s",
            _trace_id(request),
            exc.code,
            request.url.path,
        )
        return _response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            retryable=exc.retryable,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _response(
            request,
            status_code=422,
            code="EVENT_INPUT_INVALID",
            message="Request validation failed.",
            details={"fields": exc.errors()},
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        code = "HTTP_ERROR"
        message = str(detail)
        details = None
        if isinstance(detail, dict):
            code = str(detail.get("code", code))
            message = str(detail.get("message", "Request failed."))
            details = detail.get("details")
        elif exc.status_code == 401:
            code = "AUTH_INVALID_CREDENTIALS"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        return _response(
            request,
            status_code=exc.status_code,
            code=code,
            message=message,
            details=details,
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_request_error trace_id=%s path=%s",
            _trace_id(request),
            request.url.path,
            exc_info=exc,
        )
        return _response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An internal error occurred.",
        )
