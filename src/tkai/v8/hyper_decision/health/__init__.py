from tkai.v8.hyper_decision.fabric import HyperDecisionFabric


def health_report(fabric: HyperDecisionFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_report",)
