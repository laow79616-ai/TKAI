from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def audit_snapshot(mesh: AdaptiveDecisionMesh) -> tuple[dict[str, object], ...]:
    return mesh.observability.audit_records()


__all__ = ("audit_snapshot",)
