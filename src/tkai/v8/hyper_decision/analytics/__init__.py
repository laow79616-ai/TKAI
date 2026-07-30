from tkai.v8.hyper_decision.fabric import HyperDecisionFabric


def coverage_summary(fabric: HyperDecisionFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("coverage_summary",)
