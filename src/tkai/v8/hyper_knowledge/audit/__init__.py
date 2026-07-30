from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric


def audit_records(
    fabric: HyperKnowledgeFabric,
) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()


__all__ = ("audit_records",)
