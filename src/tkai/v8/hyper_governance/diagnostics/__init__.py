"""Governance diagnostics projection."""

from __future__ import annotations

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric


def diagnostics(fabric: HyperGovernanceFabric) -> tuple[dict[str, object], ...]:
    return fabric.diagnostics()


__all__ = ("diagnostics",)
