from tkai.v8.hyper_decision.fabric import HyperDecisionFabric


def metric_snapshot(fabric: HyperDecisionFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metric_snapshot",)
