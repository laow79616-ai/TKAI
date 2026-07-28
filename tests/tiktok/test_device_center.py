from __future__ import annotations

from typing import Any

import pytest

from tiktok.device_center import (
    AllocationPolicy,
    Device,
    DeviceGroup,
    DeviceProfile,
    DeviceScope,
    DeviceStatus,
    DeviceType,
    HealthSnapshot,
    RecoveryPolicy,
    TikTokDeviceCenter,
)
from tiktok.device_center.adapters import ReferenceDeviceRuntime
from tiktok.device_center.api import ROUTES, register_device_center_routes
from tiktok.device_center.metrics import METRIC_NAMES


def scope(workspace: str = "workspace-a") -> DeviceScope:
    return DeviceScope(
        "tenant-a",
        workspace,
        "operator",
        frozenset({"tiktok:device-center:admin"}),
    )


def device(identifier: str, kind: DeviceType = DeviceType.ANDROID) -> Device:
    return Device(
        identifier,
        f"Device {identifier}",
        kind,
        "Android" if kind is not DeviceType.IPHONE else "iOS",
        "Reference Model",
        f"encrypted-reference://serial/{identifier}",
        "tenant-a",
        "workspace-a",
        "owner",
    )


def ready(center: TikTokDeviceCenter, value: Device) -> None:
    center.register_device(value, scope())
    center.transition(value.id, DeviceStatus.PROVISIONING, scope())
    center.transition(value.id, DeviceStatus.READY, scope())


def test_lifecycle_inventory_profiles_groups_and_secret_redaction() -> None:
    center = TikTokDeviceCenter()
    value = device("one")
    value.metadata = {"rack": "local", "token": "unsafe"}
    center.register_device(value, scope())
    assert value.metadata == {"rack": "local"}
    center.transition(value.id, DeviceStatus.PROVISIONING, scope())
    center.transition(value.id, DeviceStatus.READY, scope())
    profile = DeviceProfile(
        "profile-1",
        "English Android",
        "tenant-a",
        "workspace-a",
        "1080x1920",
        "en",
        "UTC",
        "en-US",
        "US",
        "android-reference",
    )
    center.create_profile(profile, scope())
    center.assign_profile(value.id, profile.id, scope())
    group = DeviceGroup(
        "group-1", "Primary", "tenant-a", "workspace-a", "owner"
    )
    center.create_group(group, scope())
    center.add_to_group(value.id, group.id, scope())
    assert value.profile_id == profile.id
    assert value.id in group.device_ids
    with pytest.raises(ValueError):
        center.transition(value.id, DeviceStatus.DELETED, scope())


def test_mock_discovery_and_workspace_isolation() -> None:
    runtime = ReferenceDeviceRuntime(
        [
            {
                "id": "discovered-1",
                "name": "Mock emulator",
                "type": "android_emulator",
                "platform": "Android",
                "model": "Mock",
                "serial_reference": "encrypted-reference://serial/mock",
            }
        ]
    )
    center = TikTokDeviceCenter(runtime=runtime)
    assert center.discover(scope())[0].type is DeviceType.ANDROID_EMULATOR
    with pytest.raises(PermissionError):
        center.transition(
            "discovered-1", DeviceStatus.PROVISIONING, scope("workspace-b")
        )


def test_priority_scheduling_allocation_affinity_release_and_cooldown() -> None:
    center = TikTokDeviceCenter(
        allocation=AllocationPolicy(
            maximum_concurrent_devices=2,
            workspace_limit=2,
            account_limit=1,
            cooldown_seconds=10,
        )
    )
    ready(center, device("one"))
    ready(center, device("two"))
    center.enqueue(
        scope(), requester="workflow-low", account_reference="account-1", priority=1
    )
    center.enqueue(
        scope(), requester="workflow-high", account_reference="account-2", priority=9
    )
    reservations = center.allocate(scope(), limit=2)
    assert [item.requester for item in reservations] == [
        "workflow-high",
        "workflow-low",
    ]
    released = center.release(reservations[0].id, scope())
    assert released.status is DeviceStatus.READY
    assert released.cooldown_until is not None


def test_expired_reservation_is_released_before_new_allocation() -> None:
    center = TikTokDeviceCenter(
        allocation=AllocationPolicy(
            maximum_concurrent_devices=1,
            workspace_limit=1,
            account_limit=1,
            reservation_timeout_seconds=0,
            cooldown_seconds=0,
        )
    )
    ready(center, device("one"))
    center.enqueue(
        scope(), requester="workflow-one", account_reference="account-1"
    )
    first = center.allocate(scope())[0]
    center.enqueue(
        scope(), requester="workflow-two", account_reference="account-2"
    )
    second = center.allocate(scope())[0]
    assert first.released_at is not None
    assert second.device_id == "one"


def test_health_telemetry_failure_detection_and_statistics() -> None:
    center = TikTokDeviceCenter()
    ready(center, device("one"))
    snapshot = center.record_health(
        HealthSnapshot(
            "one", True, 75, 25, 40, 30, 120, "sensor-reference://temperature/one"
        ),
        scope(),
    )
    assert snapshot.score == 100
    assert center.health(scope())["score"] == 100
    statistics = center.statistics(scope())
    assert statistics["available_devices"] == 1
    assert statistics["average_runtime"] == 120
    assert center.metrics.values["tiktok_device_cpu_usage"] == 25

    failed = center.record_health(
        HealthSnapshot("one", False, 10, 99, 99, 99, 121),
        scope(),
    )
    assert failed.failed
    assert center.devices["one"].status is DeviceStatus.OFFLINE
    assert center.metrics.values["tiktok_device_failures"] == 1


class RestrictedRisk:
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool:
        return True


def test_recovery_stops_for_unresolved_tiktok_restrictions() -> None:
    center = TikTokDeviceCenter(risk_control=RestrictedRisk())
    value = device("one")
    value.account_reference = "account-reference://one"
    ready(center, value)
    record = center.recover("one", scope(), reason="unresolved challenge")
    assert record.stopped_for_restriction
    assert record.manual_approval_required
    assert not record.recovered
    assert center.devices["one"].status is DeviceStatus.PAUSED


class FailingRuntime(ReferenceDeviceRuntime):
    def reconnect(self, device: Device) -> bool:
        return False

    def restart(self, device: Device) -> bool:
        return False

    def reinitialize(self, device: Device) -> bool:
        return False

    def reload_profile(self, device: Device) -> bool:
        return False


def test_recovery_is_bounded_and_supports_manual_approval() -> None:
    center = TikTokDeviceCenter(
        runtime=FailingRuntime(),
        recovery=RecoveryPolicy(maximum_attempts=1, manual_approval=True),
    )
    ready(center, device("one"))
    pending = center.recover("one", scope(), reason="offline")
    assert pending.manual_approval_required
    attempted = center.recover("one", scope(), reason="offline", approved=True)
    assert attempted.actions == (
        "reconnect",
        "restart",
        "reinitialize",
        "reload_profile",
    )
    assert not attempted.recovered
    stopped = center.recover("one", scope(), reason="offline", approved=True)
    assert stopped.actions == ("manual_approval",)


def test_dashboard_api_metrics_and_integration_notifications() -> None:
    class Integration:
        def __init__(self) -> None:
            self.events: list[str] = []

        def notify(
            self, event: str, device_reference: str, context: dict[str, str]
        ) -> None:
            self.events.append(event)

    integration = Integration()
    center = TikTokDeviceCenter(
        integrations={
            name: integration
            for name in (
                "browser_cluster",
                "browser_runtime",
                "account_center",
                "proxy_center",
                "workflow_center",
                "operations_center",
                "risk_control_center",
            )
        }
    )
    center.register_device(device("one"), scope())
    dashboard = center.dashboard(scope())
    assert dashboard["sections"] == [
        "Overview",
        "Devices",
        "Groups",
        "Profiles",
        "Queues",
        "Resources",
        "Health",
        "Recovery",
        "Telemetry",
        "Statistics",
    ]
    assert set(METRIC_NAMES) == set(center.metrics.values)
    assert len(integration.events) == 7

    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(
            self, path: str, handler: Any, methods: list[str]
        ) -> None:
            self.paths.append(path)

    app = App()
    register_device_center_routes(app, center)
    assert tuple(app.paths) == ROUTES
