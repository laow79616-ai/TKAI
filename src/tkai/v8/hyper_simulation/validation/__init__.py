from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric


def validate_horizon(fabric: HyperSimulationFabric, horizon: int) -> bool:
    fabric.validate_time_horizon(horizon)
    return True
