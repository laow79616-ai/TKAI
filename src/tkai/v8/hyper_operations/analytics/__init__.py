"""Read-only operations analytics."""

from typing import cast

from tkai.v8.hyper_operations.fabric import HyperOperationsFabric


def analytics_snapshot(fabric: HyperOperationsFabric) -> dict[str, object]:
    value = cast(dict[str, object], fabric.snapshot()["analytics"])
    return dict(value)
