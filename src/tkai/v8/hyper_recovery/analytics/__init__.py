from tkai.v8.hyper_recovery.fabric import HyperRecoveryFabric


def analytics_snapshot(fabric: HyperRecoveryFabric) -> dict[str, object]:
    return fabric.snapshot()["analytics"]  # type: ignore[return-value]
