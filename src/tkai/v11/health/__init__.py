"""Health projection helpers."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore


def health(core: AutonomousIntelligenceCore) -> dict[str, object]:
    return core.health()


__all__ = ("health",)
