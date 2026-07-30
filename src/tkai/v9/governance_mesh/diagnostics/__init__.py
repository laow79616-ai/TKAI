"""Governance diagnostics projection."""

from __future__ import annotations

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh


def diagnostics(fabric: AdaptiveGovernanceMesh) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostics",)

