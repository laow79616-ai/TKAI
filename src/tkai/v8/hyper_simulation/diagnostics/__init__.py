from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric


def diagnostic_report(fabric: HyperSimulationFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()
