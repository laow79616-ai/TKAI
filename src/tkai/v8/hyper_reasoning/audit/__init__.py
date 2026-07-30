from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric


def audit_records(
    fabric: HyperReasoningFabric,
) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)
