"""Governance metadata helpers."""

from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh


def governance_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return mesh.governance()


__all__ = ("governance_snapshot",)
