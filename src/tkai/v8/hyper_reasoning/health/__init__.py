from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric


def health(fabric: HyperReasoningFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health",)
