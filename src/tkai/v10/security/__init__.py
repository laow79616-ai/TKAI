"""Local-only security guards for safe sovereign metadata."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v10.contracts import Scope

SECRET_MARKERS = (
    "password",
    "cookie",
    "session",
    "proxy_credential",
    "api_key",
    "secret",
    "token",
)


def filter_secrets(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(marker in str(key).lower() for marker in SECRET_MARKERS)
                else filter_secrets(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [filter_secrets(item) for item in value]
    return value


def authorize_scope(requested: Scope, available: Scope) -> None:
    for field, message in (
        ("tenant", "tenant isolation"),
        ("workspace", "workspace isolation"),
        ("namespace", "namespace isolation"),
    ):
        if getattr(requested, field) != getattr(available, field):
            raise PermissionError(message)


def validate_safe_metadata(metadata: Mapping[str, object]) -> None:
    for key in metadata:
        if any(marker in key.lower() for marker in SECRET_MARKERS):
            raise ValueError(f"secret-bearing metadata is forbidden: {key}")


__all__ = (
    "SECRET_MARKERS",
    "authorize_scope",
    "filter_secrets",
    "validate_safe_metadata",
)
