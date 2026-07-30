"""Governance metrics projection."""

from __future__ import annotations

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh


def metrics(fabric: AdaptiveGovernanceMesh) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics",)
