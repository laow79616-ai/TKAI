from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def diagnostics_snapshot(mesh: AdaptiveDecisionMesh) -> tuple[dict[str, object], ...]:
    return mesh.diagnostics()


__all__ = ("diagnostics_snapshot",)
