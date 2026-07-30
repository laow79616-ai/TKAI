from tkai.v8.hyper_planning.fabric import HyperPlanningFabric


def coverage_summary(fabric: HyperPlanningFabric) -> dict[str, object]:
    return {"registries": fabric.metrics(), "supported_generations": ("v6", "v7", "v8")}


__all__ = ("coverage_summary",)
