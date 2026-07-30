"""Metrics projection helpers."""

from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh


def metrics_snapshot(fabric: AdaptiveIntelligenceMesh) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics_snapshot",)
