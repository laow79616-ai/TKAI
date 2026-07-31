"""Metrics projection helpers."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore


def metrics(core: AutonomousIntelligenceCore) -> dict[str, int | float]:
    return core.metrics()


__all__ = ("metrics",)
