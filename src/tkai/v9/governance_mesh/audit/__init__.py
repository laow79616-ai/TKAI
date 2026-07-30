"""Read-only audit projection helpers."""

from __future__ import annotations

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh


def audit_records(fabric: AdaptiveGovernanceMesh) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)

