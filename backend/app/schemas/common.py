"""Common schemas shared across API responses."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Machine-readable error payload."""

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: Optional[Any] = Field(None, description="Additional context.")
    retryable: bool = Field(False, description="Whether the caller should retry.")
    trace_id: str = Field(..., description="Request correlation identifier.")


class ErrorResponse(BaseModel):
    """Stable API error envelope."""

    error: ErrorBody


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    total: int
    page: int
    per_page: int
    items: list[Any]
