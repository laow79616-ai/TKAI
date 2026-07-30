"""Read-only dashboard projections."""

from tkai.v8.hyper_recovery.api import PROJECTIONS
from tkai.v8.hyper_recovery.fabric import HyperRecoveryFabric

DASHBOARD_SECTIONS = (
    "overview",
    *PROJECTIONS,
)


def dashboard_snapshot(fabric: HyperRecoveryFabric) -> dict[str, object]:
    snapshot = fabric.snapshot()
    return {name: snapshot[name] for name in DASHBOARD_SECTIONS}
