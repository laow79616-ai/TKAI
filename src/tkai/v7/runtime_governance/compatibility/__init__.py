"""V6 compatibility projection."""

from ..framework import RuntimeGovernanceFramework


def v6_compatibility() -> dict[str, object]:
    return RuntimeGovernanceFramework().compatibility()


__all__ = ("v6_compatibility",)
