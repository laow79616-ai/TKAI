from tkai.v8.hyper_decision.contracts import ApprovalMetadata


def authorizes_execution(_approval: ApprovalMetadata | None = None) -> bool:
    return False


__all__ = ("ApprovalMetadata", "authorizes_execution")
