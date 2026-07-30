from tkai.v8.hyper_planning.fabric import HyperPlanningFabric


def metric_snapshot(fabric: HyperPlanningFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metric_snapshot",)
