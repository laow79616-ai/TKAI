"""Metrics projection helpers."""

from tkai.v8.hyper_intelligence.fabric import HyperIntelligenceFabric


def metrics_snapshot(fabric: HyperIntelligenceFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics_snapshot",)
