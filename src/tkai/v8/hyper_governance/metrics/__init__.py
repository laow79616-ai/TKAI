"""Governance metrics projection."""

from __future__ import annotations

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric


def metrics(fabric: HyperGovernanceFabric) -> dict[str, object]:
    return fabric.metrics()


__all__ = ("metrics",)
