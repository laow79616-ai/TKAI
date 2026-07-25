"""Minimal request-id and safe error-response helpers for the Studio host."""

from __future__ import annotations

from uuid import uuid4

from .errors import (
    StudioConflictError,
    StudioError,
    StudioNotFoundError,
    StudioUnavailableError,
    StudioValidationError,
)


def request_id(value: str | None) -> str:
    """Reuse a non-empty caller request id or generate a safe local identifier."""
    return value.strip() if value is not None and value.strip() else str(uuid4())


def error_status(error: StudioError) -> int:
    """Map stable Studio error types to REST status codes without stack traces."""
    if isinstance(error, StudioNotFoundError):
        return 404
    if isinstance(error, StudioConflictError):
        return 409
    if isinstance(error, StudioValidationError):
        return 422
    if isinstance(error, StudioUnavailableError):
        return 503
    return 500


def error_payload(error: StudioError, request_identifier: str) -> dict[str, str]:
    """Return a stable, non-sensitive error response body."""
    return {
        "error": error.__class__.__name__,
        "message": str(error),
        "request_id": request_identifier,
    }
