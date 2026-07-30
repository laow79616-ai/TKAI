from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def history_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return mesh.history()


__all__ = ("history_snapshot",)
