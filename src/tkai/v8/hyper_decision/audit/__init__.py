from tkai.v8.hyper_decision.fabric import HyperDecisionFabric


def audit_records(fabric: HyperDecisionFabric) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)
