"""Offline regression coverage for optional V1.2 local distributed runtime."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Thread

from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.distributed import (
    DistributedCoordinator,
    DistributedPolicyAdapter,
    DistributedRuntimeAdapter,
    LocalBackend,
    Membership,
    Node,
    NodeStatus,
)
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage


def node(name: str = "node") -> Node:
    """Create deterministic UTC-safe local membership test data."""
    now = datetime.now(timezone.utc)
    return Node(name, "localhost", now, now, frozenset({"local"}))


def test_local_backend_sync_pubsub_and_thread_safety() -> None:
    """Exercise local backend data, notifications, locks, and concurrent writes."""
    backend = LocalBackend()
    backend.connect()
    received: list[str] = []
    backend.subscribe("topic", received.append)
    backend.set("key", "value")
    backend.publish("topic", "value")
    workers = [
        Thread(target=backend.set, args=(f"key-{number}", number))
        for number in range(25)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    assert backend.get("key") == "value"
    assert received == ["value"]
    assert backend.acquire_lock("lock", "one")
    assert not backend.acquire_lock("lock", "two")
    assert backend.release_lock("lock", "one")
    assert backend.health()


def test_membership_heartbeat_expiry_and_events_are_local() -> None:
    """Validate membership lifecycle, cooperative heartbeat, and expiry simulation."""
    bus = EventBus()
    membership = Membership(event_bus=bus)
    original = node("one")
    membership.register(original)
    updated = membership.heartbeat("one")
    expired = membership.snapshot(
        expiry=timedelta(seconds=0), now=updated.last_seen + timedelta(seconds=1)
    )
    assert expired[0].status is NodeStatus.EXPIRED
    membership.unregister("one")
    assert [event.name for event in bus.events] == [
        "NodeJoined",
        "HeartbeatUpdated",
        "NodeLeft",
    ]
    assert original.to_dict()["status"] == "active"


def test_coordinator_locks_runtime_and_policy_adapters_are_explicit() -> None:
    """No distributed state starts until the caller explicitly starts the adapter."""
    bus = EventBus()
    coordinator = DistributedCoordinator(node(), event_bus=bus)
    runtime = DistributedRuntimeAdapter(coordinator)
    assert not runtime.health()["started"]
    runtime.start()
    lock = coordinator.lock("resource")
    assert lock.acquire()
    assert lock.renew()
    assert lock.release()

    policies = PolicyManager()
    policies.register(DistributedPolicyAdapter(coordinator))
    context = PolicyContext(PolicyStage.BEFORE_REQUEST)
    policies.execute(context)
    assert context.data["distributed_coordinator"] is coordinator
    runtime.stop()
    assert any(event.name == "CoordinatorStarted" for event in bus.events)
    assert any(event.name == "CoordinatorStopped" for event in bus.events)


def test_doctor_cli_and_serialized_summary_are_read_only(monkeypatch) -> None:
    """Present coordinator diagnostics without taking ownership of its lifecycle."""
    coordinator = DistributedCoordinator(node())
    report = DoctorService(distributed=coordinator).run()
    check = next(
        item for item in report.checks if item.name == "distributed.coordinator"
    )
    assert check.status is DoctorStatus.WARNING
    assert check.detail["backend"] == "LocalBackend"
    monkeypatch.setattr(
        ai_commands, "_service", AICommandService(distributed=coordinator)
    )
    result = CliRunner().invoke(ai_commands.app, ["distributed", "--json"])
    assert result.exit_code == 0
    assert '"backend": "LocalBackend"' in result.stdout
