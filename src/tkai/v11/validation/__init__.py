"""Validation projection helpers."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore


def validate(core: AutonomousIntelligenceCore) -> dict[str, object]:
    return core.validation()


__all__ = ("validate",)
