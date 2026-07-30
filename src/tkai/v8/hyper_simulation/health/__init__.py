from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric


def health_report(fabric: HyperSimulationFabric) -> dict[str, object]:
    return fabric.health()
