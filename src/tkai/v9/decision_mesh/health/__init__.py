from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def health_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return mesh.health()


__all__ = ("health_snapshot",)
