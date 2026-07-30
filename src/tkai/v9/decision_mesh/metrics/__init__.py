from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def metrics_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return mesh.metrics()


__all__ = ("metrics_snapshot",)
