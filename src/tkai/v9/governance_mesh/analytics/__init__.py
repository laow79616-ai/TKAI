"""Read-only governance coverage analytics."""

from __future__ import annotations

from tkai.v9.governance_mesh.contracts import ComplianceRecord


def coverage_summary(record: ComplianceRecord) -> dict[str, float]:
    """Return normalized coverage dimensions without making a decision."""

    return {
        "policy": record.policy_coverage,
        "constraint": record.constraint_coverage,
        "compatibility": record.compatibility_coverage,
        "review": record.review_coverage,
        "approval": record.approval_coverage,
        "audit": record.audit_coverage,
    }


__all__ = ("coverage_summary",)
