"""Health projection helpers."""

from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh


def health_snapshot(fabric: AdaptiveKnowledgeMesh) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_snapshot",)
