"""Governance health projection."""

from __future__ import annotations

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh


def health(fabric: AdaptiveGovernanceMesh) -> dict[str, object]:
    return fabric.health()


__all__ = ("health",)
