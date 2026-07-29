"""Governance health projection."""

from __future__ import annotations

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric


def health(fabric: HyperGovernanceFabric) -> dict[str, object]:
    return fabric.health()


__all__ = ("health",)
