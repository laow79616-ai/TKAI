"""Read-only audit projection helpers."""

from __future__ import annotations

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric


def audit_records(fabric: HyperGovernanceFabric) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)
