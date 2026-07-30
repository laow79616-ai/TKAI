from tkai.v8.hyper_planning.fabric import HyperPlanningFabric


def diagnostic_report(fabric: HyperPlanningFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostic_report",)
