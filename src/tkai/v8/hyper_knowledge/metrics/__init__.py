from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric


def metrics(fabric: HyperKnowledgeFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics",)
