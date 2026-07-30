from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric


def audit_records(fabric: HyperSimulationFabric) -> tuple[dict[str, object], ...]:
    return fabric.observability.audit_records()
