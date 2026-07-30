"""Non-authorizing approval metadata services."""

from tkai.v9.governance_mesh.contracts import ApprovalRecord


def authorizes_execution(_: ApprovalRecord) -> bool:
    return False


__all__ = ("ApprovalRecord", "authorizes_execution")
