"""Health projection helpers."""

from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh


def health_snapshot(fabric: AdaptiveIntelligenceMesh) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_snapshot",)
