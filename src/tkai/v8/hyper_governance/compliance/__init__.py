"""Coverage-only compliance metadata services."""

from tkai.v8.hyper_governance.contracts import ComplianceRecord


def enforces_compliance(_: ComplianceRecord) -> bool:
    return False


__all__ = ("ComplianceRecord", "enforces_compliance")
