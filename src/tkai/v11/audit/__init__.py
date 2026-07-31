"""Immutable audit projection helpers."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore


def audit(core: AutonomousIntelligenceCore) -> dict[str, object]:
    return core.audit()


__all__ = ("audit",)
