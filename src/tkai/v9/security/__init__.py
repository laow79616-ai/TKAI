"""Local boundary, isolation and safe-metadata enforcement."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta

from tkai.v9.contracts import Context, Scope

SECRET_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "cookie",
    "session",
    "proxy",
)


def filter_secrets(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if any(marker in str(key).lower() for marker in SECRET_MARKERS)
            else filter_secrets(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [filter_secrets(item) for item in value]
    return value


def authorize_scope(principal: Scope, requested: Scope) -> None:
    for field in ("tenant", "workspace", "namespace"):
        if getattr(principal, field) != getattr(requested, field):
            raise PermissionError(f"{field} isolation violation")


def validate_context(
    context: Context, *, max_range: timedelta = timedelta(days=366)
) -> None:
    if context.time_range:
        start, end = context.time_range
        if end < start or end - start > max_range:
            raise ValueError("bounded time range exceeded")
    filtered = filter_secrets(context.safe_metadata)
    if filtered != dict(context.safe_metadata):
        raise ValueError("safe metadata contains secret-like fields")


__all__ = ("authorize_scope", "filter_secrets", "validate_context")
