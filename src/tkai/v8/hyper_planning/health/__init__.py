from tkai.v8.hyper_planning.fabric import HyperPlanningFabric


def health_report(fabric: HyperPlanningFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_report",)
