from tkai.v8.hyper_decision.fabric import HyperDecisionFabric


def diagnostic_report(fabric: HyperDecisionFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostic_report",)
