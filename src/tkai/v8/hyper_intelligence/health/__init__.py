"""Health projection helpers."""

from tkai.v8.hyper_intelligence.fabric import HyperIntelligenceFabric


def health_snapshot(fabric: HyperIntelligenceFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health_snapshot",)
