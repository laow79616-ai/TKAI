"""Coverage-only compliance metadata services."""

from tkai.v9.governance_mesh.contracts import ComplianceRecord


def enforces_compliance(_: ComplianceRecord) -> bool:
    return False


__all__ = ("ComplianceRecord", "enforces_compliance")

