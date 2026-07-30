from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric


def analytics_snapshot(fabric: HyperSimulationFabric) -> dict[str, object]:
    return fabric.analytics()
