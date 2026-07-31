"""Diagnostics projection helpers."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore


def diagnose(core: AutonomousIntelligenceCore) -> dict[str, object]:
    return core.diagnostics()


__all__ = ("diagnose",)
