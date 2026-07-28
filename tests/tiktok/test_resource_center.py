from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.resource_center import (
    HealthState,
    Priority,
    Quota,
    Resource,
    ResourceScope,
    ResourceStatus,
    ResourceType,
    TikTokResourceCenter,
    UtilizationSample,
)
from tiktok.resource_center.api import ROUTES, register_resource_center_routes
from tiktok.resource_center.metrics import METRIC_NAMES
from tiktok.resource_center.models import utcnow


def scope(workspace: str = "w1") -> ResourceScope:
    return ResourceScope(
        "tenant-1", workspace, "operator", frozenset({"tiktok:resources:admin"})
    )


def resource(
    reference: str,
    resource_type: ResourceType = ResourceType.BROWSER,
    workspace: str = "w1",
    **kwargs: Any,
) -> Resource:
    return Resource(
        reference,
        f"Resource {reference}",
        resource_type,
        "tenant-1",
        workspace,
        "owner",
        **kwargs,
    )


def test_inventory_registration_search_lifecycle_validation_and_isolation() -> None:
    center = TikTokResourceCenter()
    item = center.register(
        resource(
            "browser-1",
            tags=frozenset({"production", "chrome"}),
            group="browser-pool",
            encrypted_reference="vault://browser/1",
            metadata={"region": "local"},
        ),
        scope(),
    )
    assert item.status is ResourceStatus.REGISTERED
    assert center.search(scope(), query="browser", tags=frozenset({"chrome"})) == [
        item
    ]
    assert center.transition(item.id, ResourceStatus.IDLE, scope()).version == 2
    assert center.transition(item.id, ResourceStatus.PAUSED, scope()).version == 3
    assert center.search(scope("other")) == []
    with pytest.raises(ValueError):
        center.register(resource("unsafe", metadata={"token": "plaintext"}), scope())
    with pytest.raises(ValueError):
        center.register(resource("code", metadata={"command": "whoami"}), scope())
    with pytest.raises(ValueError):
        center.register(
            resource("plain-reference", encrypted_reference="https://secret"), scope()
        )


def test_discovery_classification_version_group_and_bounded_integrations() -> None:
    class DiscoveryPort:
        def discover(self, request_scope: ResourceScope) -> list[Resource]:
            return [
                resource("device-1", ResourceType.DEVICE),
                resource("worker-1", ResourceType.WORKER),
            ]

    center = TikTokResourceCenter({"device_center": DiscoveryPort()})
    discovered = center.discover(scope())
    assert {item.id for item in discovered} == {"device-1", "worker-1"}
    assert all(item.status is ResourceStatus.DISCOVERED for item in discovered)
    assert all(item.metadata["source"] == "device_center" for item in discovered)
    assert not any(
        name in center.ports
        for name in ("telegram", "whatsapp", "facebook", "instagram", "discord")
    )
    with pytest.raises(ValueError):
        TikTokResourceCenter({"unbounded_platform": DiscoveryPort()})


def test_reservation_conflicts_heartbeat_renewal_cancellation_and_timeout() -> None:
    center = TikTokResourceCenter()
    center.register(resource("browser"), scope())
    reservation = center.reserve(
        "browser", "owner-a", scope(), duration_seconds=60, priority=Priority.HIGH
    )
    assert center.resources["browser"].status is ResourceStatus.RESERVED
    with pytest.raises(RuntimeError):
        center.reserve("browser", "owner-b", scope())
    old_expiration = reservation.expires_at
    center.heartbeat_reservation(reservation.id, scope(), 120)
    assert reservation.expires_at > old_expiration
    center.cancel_reservation(reservation.id, scope())
    assert reservation.cancelled
    assert center.resources["browser"].status is ResourceStatus.RELEASED
    second = center.reserve("browser", "owner-b", scope())
    second.expires_at = utcnow() - timedelta(seconds=1)
    assert center.cleanup_expired(scope())["reservations"] == 1


def test_allocation_lease_renewal_expiration_release_cooldown_and_ownership() -> None:
    center = TikTokResourceCenter()
    center.register(resource("device", ResourceType.DEVICE), scope())
    reservation = center.reserve("device", "owner", scope())
    allocation, lease = center.allocate(
        "device",
        "owner",
        scope(),
        reservation_id=reservation.id,
        lease_seconds=60,
    )
    assert center.resources["device"].status is ResourceStatus.ALLOCATED
    old_expiration = lease.expires_at
    center.renew_lease(lease.id, "owner", scope(), 120)
    assert lease.expires_at > old_expiration
    with pytest.raises(RuntimeError):
        center.renew_lease(lease.id, "other", scope())
    released = center.release(allocation.id, "owner", scope(), cooldown_seconds=30)
    assert released.cooldown_until and released.cooldown_until > utcnow()
    assert not lease.active
    assert center.resources["device"].status is ResourceStatus.RELEASED
    with pytest.raises(RuntimeError, match="cooldown"):
        center.allocate("device", "owner", scope())

    center.register(resource("worker", ResourceType.WORKER), scope())
    _, expiring_lease = center.allocate("worker", "owner", scope())
    expiring_lease.expires_at = utcnow() - timedelta(seconds=1)
    assert center.cleanup_expired(scope())["leases"] == 1
    assert center.resources["worker"].status is ResourceStatus.RELEASED


def test_approval_enforcement_uses_opaque_references() -> None:
    center = TikTokResourceCenter()
    center.register(
        resource("approved", metadata={"requires_approval": True}), scope()
    )
    with pytest.raises(PermissionError):
        center.allocate("approved", "owner", scope())
    with pytest.raises(ValueError):
        center.allocate(
            "approved", "owner", scope(), approval_reference="plaintext-approval"
        )
    allocation, _ = center.allocate(
        "approved", "owner", scope(), approval_reference="approval://change-1"
    )
    assert allocation.resource_id == "approved"


def test_quotas_capacity_utilization_health_telemetry_and_statistics() -> None:
    center = TikTokResourceCenter(default_quota=Quota(workspace=2, browser=1))
    center.register(
        resource(
            "browser",
            maximum_capacity=4,
            health=HealthState.HEALTHY,
        ),
        scope(),
    )
    with pytest.raises(OverflowError):
        center.register(resource("browser-2"), scope())
    center.register(
        resource(
            "proxy",
            ResourceType.PROXY,
            maximum_capacity=2,
            health=HealthState.DEGRADED,
        ),
        scope(),
    )
    center.allocate("browser", "owner", scope())
    sample = center.record_utilization(
        UtilizationSample(
            "tenant-1",
            "w1",
            cpu=0.5,
            memory=0.4,
            browser_slots=0.5,
            devices=0.1,
            workers=0.2,
            queue_usage=0.3,
            proxy_usage=0.2,
            account_usage=0.1,
        ),
        scope(),
    )
    assert sample.ratio > 0
    capacity = center.capacity(scope())
    assert capacity["maximum_capacity"] == 6
    assert capacity["allocated_capacity"] == 4
    health = center.health(scope())
    assert 0 <= health["composite_health_score"] <= 100
    telemetry = center.telemetry(scope())
    assert telemetry["inventory_size"] == 2
    assert center.statistics(scope())["allocation_rate"] == 0.5


def test_recovery_reconciliation_restriction_stop_retry_and_metrics() -> None:
    center = TikTokResourceCenter()
    item = center.register(
        resource("runtime", ResourceType.RUNTIME, health=HealthState.UNHEALTHY),
        scope(),
    )
    center.transition(item.id, ResourceStatus.IDLE, scope())
    assert center.recover(item.id, scope()).health is HealthState.HEALTHY
    blocked = center.register(
        resource(
            "restricted",
            ResourceType.ACCOUNT,
            restriction_active=True,
            health=HealthState.UNHEALTHY,
        ),
        scope(),
    )
    center.transition(blocked.id, ResourceStatus.IDLE, scope())
    with pytest.raises(RuntimeError, match="Recovery stopped"):
        center.recover(blocked.id, scope())
    assert center.failures[-1]["reason"].startswith("unresolved_tiktok")
    center.reconcile(scope())
    assert center.metrics.values["tiktok_resource_recovery_total"] == 1


def test_api_dashboard_metrics_and_security_contract() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    center = TikTokResourceCenter()
    register_resource_center_routes(app, center)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/resource-center/dashboard" in app.routes
    assert "/tiktok/resource-center/metrics" in app.routes
    dashboard = center.dashboard(
        ResourceScope(
            "default",
            "default",
            "dashboard",
            frozenset({"tiktok:resources:admin"}),
        )
    )
    assert dashboard["safety"]["bounded_interfaces"]
    assert dashboard["safety"]["captcha_bypass"] is False
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_invalid_capacity_utilization_quota_transitions_and_durations() -> None:
    with pytest.raises(ValueError):
        resource("bad", maximum_capacity=0).validate()
    with pytest.raises(ValueError):
        Quota(workspace=-1).validate()
    with pytest.raises(ValueError):
        UtilizationSample("tenant-1", "w1", cpu=1.1).validate()
    center = TikTokResourceCenter()
    center.register(resource("browser"), scope())
    with pytest.raises(ValueError):
        center.transition("browser", ResourceStatus.RUNNING, scope())
    with pytest.raises(ValueError):
        center.reserve("browser", "owner", scope(), duration_seconds=0)
