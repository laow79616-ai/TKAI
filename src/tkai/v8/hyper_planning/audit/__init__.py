from tkai.v8.hyper_planning.fabric import HyperPlanningFabric


def audit_records(fabric: HyperPlanningFabric) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)
