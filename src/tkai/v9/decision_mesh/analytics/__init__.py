from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def analytics_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return mesh.analytics()


__all__ = ("analytics_snapshot",)
