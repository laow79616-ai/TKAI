"""Verify existing snapshots return independent containers and JSON-safe data."""

from __future__ import annotations

from datetime import datetime, timezone

from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.ai import DoctorService
from tkai.distributed import Membership, Node
from tkai.multiregion import MultiRegionManager, Region
from tkai.telemetry import Metric, TelemetryManager


def _node() -> Node:
    now = datetime.now(timezone.utc)
    return Node("local", "localhost", now, now)


def test_registry_and_metric_snapshots_do_not_expose_container_mutation() -> None:
    """Changing returned list containers cannot modify existing local state."""
    telemetry = TelemetryManager()
    telemetry.record(Metric("local", 1))
    metrics = telemetry.metrics.snapshot()
    metrics.clear()
    assert len(telemetry.metrics.snapshot()) == 1

    membership = Membership()
    membership.register(_node())
    nodes = membership.snapshot()
    nodes.clear()
    assert [node.node_id for node in membership.snapshot()] == ["local"]

    regions = MultiRegionManager()
    regions.register_region(Region("local", metadata={"source": "test"}))
    snapshot = regions.snapshot()
    snapshot["regions"] = []
    assert regions.snapshot()["regions"] != []


def test_adaptive_and_doctor_serialized_snapshots_are_independent() -> None:
    """Snapshots and report serialization return fresh JSON-ready structures."""
    adaptive = AdaptiveRoutingManager()
    adaptive.record_signal(ProviderSignal("local", datetime.now(timezone.utc)))
    snapshot = adaptive.snapshot()
    statistics = snapshot["statistics"]
    assert isinstance(statistics, list)
    statistics.clear()
    assert adaptive.snapshot()["statistics"]

    report = DoctorService(adaptive=adaptive).run()
    first = report.to_dict()
    first["summary"]["passed"] = -1
    second = report.to_dict()
    assert second["summary"]["passed"] >= 0
