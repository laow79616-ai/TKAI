"""Read-only intelligence diagnostics."""

from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh


def diagnostic_snapshot(
    mesh: AdaptiveKnowledgeMesh,
) -> tuple[dict[str, object], ...]:
    return mesh.diagnostics()


__all__ = ("diagnostic_snapshot",)
