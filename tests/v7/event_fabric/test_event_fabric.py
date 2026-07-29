from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace

import pytest

from tkai.v7.contracts import Version, VersionRange
from tkai.v7.event_fabric import (
    DeliveryMode,
    DispatchQueue,
    DispatchQueueFull,
    EventContract,
    EventEnvelope,
    EventFabric,
    EventFabricDashboard,
    EventFilter,
    EventLifecycle,
    EventModel,
    EventRegistry,
    OrderingMode,
    Publisher,
    ReplayRejected,
    ReplayRequest,
    Subscriber,
    Subscription,
)
from tkai.v7.event_fabric.api import EVENT_RESOURCES, register_event_fabric_routes


def event(identifier: str = "event-1") -> EventModel:
    return EventModel(
        event_id=identifier,
        event_type="test.created",
        event_version=Version(7),
        source="tests",
        subject="fixture",
        tenant_reference="tenant-1",
        workspace_reference="workspace-1",
        payload_reference=f"memory://payload/{identifier}",
        headers={"authorization": "hidden", "visible": "yes"},
        metadata={"session": "hidden", "kind": "test"},
    )


def fabric(handler=lambda envelope: True) -> EventFabric:
    registry = EventRegistry()
    registry.register_event(
        EventContract("test.created", Version(7), {"type": "object"})
    )
    registry.register_publisher(Publisher("publisher", frozenset({"test.created"})))
    registry.register_subscriber(Subscriber("subscriber"), handler)
    registry.register_filter(
        "test-only",
        EventFilter(
            tenants=frozenset({"tenant-1"}),
            workspaces=frozenset({"workspace-1"}),
            metadata={"kind": "test"},
        ),
    )
    registry.register_subscription(
        Subscription(
            "subscription",
            "test.created",
            VersionRange(Version(7), Version(7, 99, 99)),
            "subscriber",
            filter_reference="test-only",
            delivery_mode=DeliveryMode.AT_LEAST_ONCE,
        )
    )
    return EventFabric(registry, maximum_queue_size=2, maximum_batch_size=1)


def test_package_structure() -> None:
    packages = (
        "contracts",
        "events",
        "envelopes",
        "registry",
        "publishers",
        "subscribers",
        "subscriptions",
        "routing",
        "dispatch",
        "delivery",
        "retry",
        "dead_letter",
        "replay",
        "ordering",
        "idempotency",
        "filters",
        "policies",
        "health",
        "metrics",
        "tracing",
        "logging",
        "audit",
        "security",
        "lifecycle",
        "extensions",
        "dashboard",
        "api",
    )
    for package in packages:
        assert importlib.import_module(f"tkai.v7.event_fabric.{package}")


def test_immutable_envelope_integrity_serialization_and_secret_filtering() -> None:
    envelope = EventEnvelope.create(event(), payload_metadata={"cookie": "nope"})
    assert envelope.verify()
    assert envelope.event.headers["authorization"] == "[REDACTED]"
    assert envelope.event.metadata["session"] == "[REDACTED]"
    assert envelope.metadata["cookie"] == "[REDACTED]"
    assert EventEnvelope.deserialize(envelope.serialize()).verify()
    with pytest.raises(FrozenInstanceError):
        envelope.payload_hash = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="opaque reference"):
        EventEnvelope.create(replace(event(), payload_reference="plaintext"))


def test_routing_isolation_dispatch_delivery_and_acknowledgement() -> None:
    selected = fabric()
    envelope = selected.publish("publisher", event())
    assert selected.dispatch()[0].acknowledged
    assert selected.registry.lifecycle(envelope.event.event_id) == (
        EventLifecycle.REGISTERED,
        EventLifecycle.VALIDATED,
        EventLifecycle.PUBLISHED,
        EventLifecycle.ROUTED,
        EventLifecycle.DISPATCHED,
        EventLifecycle.DELIVERED,
        EventLifecycle.ACKNOWLEDGED,
    )
    selected.publish(
        "publisher", replace(event("outside"), workspace_reference="workspace-2")
    )
    assert selected.queue.depth == 0


def test_bounded_queue_retries_dead_letter_and_no_exactly_once() -> None:
    queue = DispatchQueue(1, 1)
    selected = fabric()
    item = (EventEnvelope.create(event()), selected.registry.subscriptions()[0])
    queue.put(item)
    with pytest.raises(DispatchQueueFull):
        queue.put(item)
    assert len(queue.batch(100)) == 1
    assert all(mode.value != "exactly_once" for mode in DeliveryMode)
    failures = fabric(lambda envelope: (_ for _ in ()).throw(RuntimeError("fail")))
    failures.publish("publisher", event("failed"))
    result = failures.dispatch()[0]
    assert not result.delivered and result.attempts == 3
    assert len(failures.retry_history) == 2
    assert len(failures.dead_letters) == 1


def test_replay_is_explicit_approved_and_bounded() -> None:
    selected = fabric()
    selected.publish("publisher", event())
    with pytest.raises(ReplayRejected, match="approval"):
        selected.replay(ReplayRequest("replay-1", event_reference="event-1"))
    assert (
        len(
            selected.replay(
                ReplayRequest(
                    "replay-2",
                    event_reference="event-1",
                    reason="review",
                    approval_reference="approval://1",
                    maximum_results=1,
                )
            )
        )
        == 1
    )
    with pytest.raises(ReplayRejected, match="exhausted"):
        selected.replay(
            ReplayRequest(
                "replay-3",
                event_reference="event-1",
                approval_reference="approval://2",
                maximum_results=1,
            )
        )


def test_ordering_metrics_health_dashboard() -> None:
    selected = fabric()
    model = event()
    assert selected.ordering_key(model, OrderingMode.NONE) is None
    assert selected.ordering_key(model, OrderingMode.SOURCE) == "tests"
    with pytest.raises(ValueError, match="partition"):
        selected.ordering_key(model, OrderingMode.PARTITION_KEY)
    selected.publish("publisher", model)
    selected.dispatch()
    snapshot = EventFabricDashboard(selected).snapshot()
    assert set(snapshot) == set(EventFabricDashboard.sections)
    assert snapshot["ordering"]["global_ordering"] is False
    assert snapshot["health"]["live"]
    assert all(name.startswith("v7_event_fabric_") for name in snapshot["metrics"])


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[object, tuple[str, ...]]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["V7 Event Fabric"]
        self.routes[path] = (handler, tuple(methods))


def test_get_only_api_has_no_public_publish_endpoint() -> None:
    app = FakeApp()
    register_event_fabric_routes(app, fabric())
    assert set(app.routes) == {f"/v7/events/{item}" for item in EVENT_RESOURCES}
    assert all(methods == ("GET",) for _, methods in app.routes.values())
    assert "/v7/events/publish" not in app.routes
    for handler, _ in app.routes.values():
        assert callable(handler)
        handler()


def test_v6_tiktok_capability_and_service_mesh_compatibility() -> None:
    assert importlib.import_module("tiktok")
    assert importlib.import_module("tkai.v7.capabilities")
    assert importlib.import_module("tkai.v7.service_mesh")
