"""Secret-safe structured logging."""

from __future__ import annotations

from collections.abc import Mapping

from tkai.v7.security import filter_secrets


def structured_event(
    event: str, service_id: str, fields: Mapping[str, object] | None = None
) -> dict[str, object]:
    return {
        "event": event,
        "service_id": service_id,
        "fields": filter_secrets(fields or {}),
    }


__all__ = ("structured_event",)
