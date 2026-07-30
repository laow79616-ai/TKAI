from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric


def metrics(fabric: HyperReasoningFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics",)
