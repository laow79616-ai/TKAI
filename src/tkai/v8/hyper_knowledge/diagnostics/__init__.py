from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric


def diagnostics(fabric: HyperKnowledgeFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostics",)
