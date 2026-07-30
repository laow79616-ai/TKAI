from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric


def health(fabric: HyperKnowledgeFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health",)
