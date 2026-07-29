"""Audit projection helpers."""

from tkai.v8.observability import Observability


def audit_snapshot(observability: Observability) -> tuple[dict[str, object], ...]:
    return observability.audit_records()


__all__ = ("audit_snapshot",)
