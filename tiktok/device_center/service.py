"""Inventory, fair scheduling, health, and bounded recovery for local devices."""
from __future__ import annotations

import heapq
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .adapters import (
    DeviceRuntimePort,
    IntegrationPort,
    NullIntegrationPort,
    PermissiveRiskControl,
    ReferenceDeviceRuntime,
    RiskControlPort,
)
from .metrics import DeviceCenterMetrics
from .models import (
    AllocationPolicy,
    Device,
    DeviceGroup,
    DeviceProfile,
    DeviceQueueItem,
    DeviceScope,
    DeviceStatus,
    DeviceType,
    HealthSnapshot,
    RecoveryPolicy,
    RecoveryRecord,
    Reservation,
    serialize,
)

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "cookie",
    "credential",
    "session",
}


class TikTokDeviceCenter:
    """Single-user local device control plane with scoped, bounded operations."""

    def __init__(
        self,
        *,
        runtime: DeviceRuntimePort | None = None,
        risk_control: RiskControlPort | None = None,
        integrations: dict[str, IntegrationPort] | None = None,
        allocation: AllocationPolicy | None = None,
        recovery: RecoveryPolicy | None = None,
    ) -> None:
        self.runtime = runtime or ReferenceDeviceRuntime()
        self.risk_control = risk_control or PermissiveRiskControl()
        self.integrations = integrations or {
            name: NullIntegrationPort()
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
        self.allocation_policy = allocation or AllocationPolicy()
        self.recovery_policy = recovery or RecoveryPolicy()
        self.allocation_policy.validate()
        self.recovery_policy.validate()
        self.devices: dict[str, Device] = {}
        self.groups: dict[str, DeviceGroup] = {}
        self.profiles: dict[str, DeviceProfile] = {}
        self.reservations: dict[str, Reservation] = {}
        self.health_snapshots: dict[str, HealthSnapshot] = {}
        self.recoveries: list[RecoveryRecord] = []
        self.audit: list[dict[str, str]] = []
        self._queue: list[DeviceQueueItem] = []
        self._sequence = 0
        self._last_workspace = ""
        self.metrics = DeviceCenterMetrics()

    @staticmethod
    def _require(scope: DeviceScope, action: str) -> None:
        required = f"tiktok:device-center:{action}"
        if required not in scope.permissions and (
            "tiktok:device-center:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(value: Any, scope: DeviceScope) -> None:
        if value.tenant != scope.tenant or value.workspace != scope.workspace:
            raise PermissionError("Cross-workspace Device Center access denied.")

    @staticmethod
    def _sanitize(metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in metadata.items()
            if not any(term in key.casefold() for term in SENSITIVE_KEYS)
        }

    def _audit(self, action: str, resource: str, scope: DeviceScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "actor": scope.actor,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def _notify(self, event: str, device: Device) -> None:
        context = {
            "tenant": device.tenant,
            "workspace": device.workspace,
            "status": device.status.value,
        }
        reference = f"device://{device.id}"
        for integration in self.integrations.values():
            integration.notify(event, reference, context)

    def register_device(self, device: Device, scope: DeviceScope) -> Device:
        self._require(scope, "write")
        self._scoped(device, scope)
        if not device.id or device.id in self.devices:
            raise ValueError("Device ID must be non-empty and unique.")
        if not all(
            (
                device.name,
                device.platform,
                device.model,
                device.serial_reference,
                device.owner,
            )
        ):
            raise ValueError("Device identity fields are required.")
        device.metadata = self._sanitize(device.metadata)
        self.devices[device.id] = device
        self._refresh_metrics()
        self._audit("device.register", device.id, scope)
        self._notify("device.discovered", device)
        return device

    def discover(self, scope: DeviceScope) -> list[Device]:
        self._require(scope, "write")
        discovered: list[Device] = []
        for record in self.runtime.discover():
            identifier = str(record["id"])
            if identifier in self.devices:
                continue
            device = Device(
                id=identifier,
                name=str(record["name"]),
                type=DeviceType(str(record["type"])),
                platform=str(record["platform"]),
                model=str(record["model"]),
                serial_reference=str(record["serial_reference"]),
                tenant=scope.tenant,
                workspace=scope.workspace,
                owner=scope.actor,
                metadata=dict(record.get("metadata", {})),
            )
            discovered.append(self.register_device(device, scope))
        return discovered

    def transition(
        self, device_id: str, status: DeviceStatus, scope: DeviceScope
    ) -> Device:
        self._require(scope, "control")
        device = self.devices[device_id]
        self._scoped(device, scope)
        allowed = {
            DeviceStatus.DISCOVERED: {
                DeviceStatus.PROVISIONING,
                DeviceStatus.OFFLINE,
                DeviceStatus.ARCHIVED,
            },
            DeviceStatus.PROVISIONING: {
                DeviceStatus.READY,
                DeviceStatus.OFFLINE,
                DeviceStatus.RECOVERING,
            },
            DeviceStatus.READY: {
                DeviceStatus.RUNNING,
                DeviceStatus.BUSY,
                DeviceStatus.PAUSED,
                DeviceStatus.OFFLINE,
                DeviceStatus.ARCHIVED,
            },
            DeviceStatus.RUNNING: {
                DeviceStatus.READY,
                DeviceStatus.BUSY,
                DeviceStatus.PAUSED,
                DeviceStatus.RECOVERING,
                DeviceStatus.OFFLINE,
            },
            DeviceStatus.BUSY: {
                DeviceStatus.READY,
                DeviceStatus.RUNNING,
                DeviceStatus.PAUSED,
                DeviceStatus.RECOVERING,
                DeviceStatus.OFFLINE,
            },
            DeviceStatus.PAUSED: {
                DeviceStatus.READY,
                DeviceStatus.RECOVERING,
                DeviceStatus.ARCHIVED,
            },
            DeviceStatus.RECOVERING: {
                DeviceStatus.READY,
                DeviceStatus.RUNNING,
                DeviceStatus.PAUSED,
                DeviceStatus.OFFLINE,
            },
            DeviceStatus.OFFLINE: {
                DeviceStatus.RECOVERING,
                DeviceStatus.READY,
                DeviceStatus.ARCHIVED,
            },
            DeviceStatus.ARCHIVED: {DeviceStatus.DELETED},
            DeviceStatus.DELETED: set(),
        }
        if status not in allowed[device.status]:
            raise ValueError(
                f"Invalid device transition: {device.status.value} -> {status.value}"
            )
        device.status = status
        self._refresh_metrics()
        self._audit("device.transition", device.id, scope)
        self._notify("device.status", device)
        return device

    def create_profile(
        self, profile: DeviceProfile, scope: DeviceScope
    ) -> DeviceProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        current = self.profiles.get(profile.id)
        if current is not None and profile.version <= current.version:
            raise ValueError("Profile version must increase.")
        self.profiles[profile.id] = profile
        self._audit("profile.version", profile.id, scope)
        return profile

    def assign_profile(
        self, device_id: str, profile_id: str, scope: DeviceScope
    ) -> Device:
        self._require(scope, "control")
        device = self.devices[device_id]
        profile = self.profiles[profile_id]
        self._scoped(device, scope)
        self._scoped(profile, scope)
        device.profile_id = profile_id
        self._audit("profile.assign", device.id, scope)
        return device

    def create_group(self, group: DeviceGroup, scope: DeviceScope) -> DeviceGroup:
        self._require(scope, "write")
        self._scoped(group, scope)
        if not group.id or group.id in self.groups or not group.name:
            raise ValueError("Group ID and name must be non-empty and unique.")
        group.metadata = self._sanitize(group.metadata)
        self.groups[group.id] = group
        self._audit("group.create", group.id, scope)
        return group

    def add_to_group(
        self, device_id: str, group_id: str, scope: DeviceScope
    ) -> None:
        self._require(scope, "control")
        device = self.devices[device_id]
        group = self.groups[group_id]
        self._scoped(device, scope)
        self._scoped(group, scope)
        group.device_ids.add(device.id)
        device.group_ids.add(group.id)
        self._audit("group.device.add", device.id, scope)

    def enqueue(
        self,
        scope: DeviceScope,
        *,
        requester: str,
        account_reference: str,
        device_type: DeviceType | None = None,
        priority: int = 0,
        delay_seconds: float = 0.0,
        attempts: int = 0,
    ) -> DeviceQueueItem:
        self._require(scope, "schedule")
        if not requester or delay_seconds < 0:
            raise ValueError("Requester is required and delay must be non-negative.")
        self._sequence += 1
        available = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        item = DeviceQueueItem(
            (-priority, available, self._sequence),
            str(uuid4()),
            scope.tenant,
            scope.workspace,
            requester,
            account_reference,
            device_type,
            priority,
            attempts,
            available,
        )
        heapq.heappush(self._queue, item)
        self._audit("queue.enqueue", item.id, scope)
        return item

    def _active_reservations(self, now: datetime) -> list[Reservation]:
        return [
            item
            for item in self.reservations.values()
            if item.released_at is None and item.expires_at > now
        ]

    def _expire_reservations(self, now: datetime) -> None:
        for reservation in self.reservations.values():
            if reservation.released_at is not None or reservation.expires_at > now:
                continue
            reservation.released_at = reservation.expires_at
            device = self.devices[reservation.device_id]
            device.status = DeviceStatus.READY
            device.reserved_by = ""
            device.reserved_until = None
            device.cooldown_until = now + timedelta(
                seconds=self.allocation_policy.cooldown_seconds
            )

    def _eligible_device(
        self, item: DeviceQueueItem, now: datetime
    ) -> Device | None:
        active_ids = {value.device_id for value in self._active_reservations(now)}
        candidates = [
            device
            for device in self.devices.values()
            if device.tenant == item.tenant
            and device.workspace == item.workspace
            and device.status is DeviceStatus.READY
            and device.id not in active_ids
            and (item.device_type is None or device.type is item.device_type)
            and (device.cooldown_until is None or device.cooldown_until <= now)
        ]
        return min(
            candidates,
            key=lambda value: (
                bool(
                    item.account_reference
                    and value.account_reference
                    and value.account_reference != item.account_reference
                ),
                value.discovered_at,
            ),
            default=None,
        )

    def allocate(
        self, scope: DeviceScope, *, limit: int | None = None
    ) -> list[Reservation]:
        self._require(scope, "schedule")
        now = datetime.now(timezone.utc)
        self._expire_reservations(now)
        maximum = self.allocation_policy.maximum_concurrent_devices
        cap = min(limit or maximum, maximum)
        active = self._active_reservations(now)
        capacity = max(0, cap - len(active))
        selected: list[Reservation] = []
        deferred: list[DeviceQueueItem] = []
        seen_workspaces: set[str] = set()
        while self._queue and len(selected) < capacity:
            item = heapq.heappop(self._queue)
            if item.available_at > now:
                deferred.append(item)
                continue
            if item.tenant != scope.tenant or item.workspace != scope.workspace:
                deferred.append(item)
                continue
            workspace_active = sum(
                value.tenant == item.tenant and value.workspace == item.workspace
                for value in (*active, *selected)
            )
            account_active = sum(
                bool(item.account_reference)
                and value.account_reference == item.account_reference
                for value in (*active, *selected)
            )
            if (
                workspace_active >= self.allocation_policy.workspace_limit
                or account_active >= self.allocation_policy.account_limit
                or (item.workspace in seen_workspaces and len(self._queue) > 0)
            ):
                deferred.append(item)
                continue
            device = self._eligible_device(item, now)
            if device is None:
                deferred.append(item)
                continue
            expires = now + timedelta(
                seconds=self.allocation_policy.reservation_timeout_seconds
            )
            reservation = Reservation(
                str(uuid4()),
                device.id,
                item.tenant,
                item.workspace,
                item.requester,
                item.account_reference,
                now,
                expires,
            )
            self.reservations[reservation.id] = reservation
            device.status = DeviceStatus.BUSY
            device.reserved_by = item.requester
            device.reserved_until = expires
            device.account_reference = item.account_reference
            selected.append(reservation)
            seen_workspaces.add(item.workspace)
            self._last_workspace = item.workspace
            self._audit("resource.reserve", device.id, scope)
            self._notify("device.reserved", device)
        for item in deferred:
            heapq.heappush(self._queue, item)
        self._refresh_metrics()
        return selected

    def release(
        self, reservation_id: str, scope: DeviceScope, *, cooldown: bool = True
    ) -> Device:
        self._require(scope, "control")
        reservation = self.reservations[reservation_id]
        self._scoped(reservation, scope)
        if reservation.released_at is not None:
            raise ValueError("Reservation is already released.")
        device = self.devices[reservation.device_id]
        self._scoped(device, scope)
        now = datetime.now(timezone.utc)
        reservation.released_at = now
        device.status = DeviceStatus.READY
        device.reserved_by = ""
        device.reserved_until = None
        device.cooldown_until = (
            now + timedelta(seconds=self.allocation_policy.cooldown_seconds)
            if cooldown
            else None
        )
        self._refresh_metrics()
        self._audit("resource.release", device.id, scope)
        self._notify("device.released", device)
        return device

    def record_health(
        self, snapshot: HealthSnapshot, scope: DeviceScope
    ) -> HealthSnapshot:
        self._require(scope, "control")
        device = self.devices[snapshot.device_id]
        self._scoped(device, scope)
        snapshot.validate()
        penalties = (
            (0 if snapshot.connectivity else 50)
            + max(0.0, 20.0 - snapshot.battery) * 0.5
            + max(0.0, snapshot.cpu - 80.0) * 0.5
            + max(0.0, snapshot.memory - 85.0) * 0.5
            + max(0.0, snapshot.storage - 90.0) * 0.5
        )
        snapshot.score = max(0.0, round(100.0 - penalties, 2))
        snapshot.failed = not snapshot.connectivity or snapshot.score < 40.0
        self.health_snapshots[device.id] = snapshot
        if snapshot.failed:
            device.status = DeviceStatus.OFFLINE
            self.metrics.increment("tiktok_device_failures")
        self._refresh_metrics()
        self._audit("health.record", device.id, scope)
        self._notify("device.health", device)
        return snapshot

    def recover(
        self,
        device_id: str,
        scope: DeviceScope,
        *,
        reason: str,
        approved: bool = False,
    ) -> RecoveryRecord:
        self._require(scope, "recover")
        device = self.devices[device_id]
        self._scoped(device, scope)
        prior = sum(
            item.device_id == device_id and item.attempt > 0
            for item in self.recoveries
        )
        restricted = self.risk_control.has_unresolved_restriction(
            scope.tenant, scope.workspace, device.account_reference
        )
        approval_required = self.recovery_policy.manual_approval and not approved
        attempts_exhausted = prior >= self.recovery_policy.maximum_attempts
        if restricted or approval_required or attempts_exhausted:
            device.status = DeviceStatus.PAUSED
            record = RecoveryRecord(
                device.id,
                prior,
                reason,
                ("manual_approval",),
                False,
                stopped_for_restriction=restricted,
                manual_approval_required=approval_required or restricted,
            )
        else:
            device.status = DeviceStatus.RECOVERING
            actions: list[str] = []
            recovered = False
            for action in ("reconnect", "restart", "reinitialize", "reload_profile"):
                actions.append(action)
                recovered = bool(getattr(self.runtime, action)(device))
                if recovered:
                    break
            device.status = DeviceStatus.READY if recovered else DeviceStatus.OFFLINE
            device.cooldown_until = datetime.now(timezone.utc) + timedelta(
                seconds=self.recovery_policy.cooldown_seconds
            )
            record = RecoveryRecord(
                device.id, prior + 1, reason, tuple(actions), recovered
            )
            if not recovered:
                self.metrics.increment("tiktok_device_failures")
        self.recoveries.append(record)
        self.metrics.increment("tiktok_device_recoveries")
        self._refresh_metrics()
        self._audit("recovery.attempt", device.id, scope)
        self._notify("device.recovery", device)
        return record

    def health(self, scope: DeviceScope) -> dict[str, Any]:
        self._require(scope, "read")
        devices = self._scope_values(self.devices, scope)
        snapshots = {
            device.id: self.health_snapshots[device.id]
            for device in devices
            if device.id in self.health_snapshots
        }
        score = (
            sum(item.score for item in snapshots.values()) / len(snapshots)
            if snapshots
            else 100.0
        )
        return {
            "score": score,
            "connectivity": {
                key: value.connectivity for key, value in snapshots.items()
            },
            "heartbeat": {
                key: value.heartbeat.isoformat() for key, value in snapshots.items()
            },
            "failures": sum(value.failed for value in snapshots.values()),
            "devices": {key: serialize(value) for key, value in snapshots.items()},
        }

    def statistics(self, scope: DeviceScope) -> dict[str, float | int]:
        self._require(scope, "read")
        devices = self._scope_values(self.devices, scope)
        snapshots = [
            self.health_snapshots[item.id]
            for item in devices
            if item.id in self.health_snapshots
        ]
        recoveries = [
            item
            for item in self.recoveries
            if item.device_id in {device.id for device in devices}
        ]
        active = sum(
            item.status in {DeviceStatus.RUNNING, DeviceStatus.BUSY}
            for item in devices
        )
        failures = sum(item.failed for item in snapshots)
        return {
            "available_devices": sum(
                item.status is DeviceStatus.READY for item in devices
            ),
            "busy_devices": sum(
                item.status is DeviceStatus.BUSY for item in devices
            ),
            "offline_devices": sum(
                item.status is DeviceStatus.OFFLINE for item in devices
            ),
            "average_runtime": (
                sum(item.runtime_seconds for item in snapshots) / len(snapshots)
                if snapshots
                else 0.0
            ),
            "failure_rate": failures / len(snapshots) if snapshots else 0.0,
            "recovery_success": (
                sum(item.recovered for item in recoveries) / len(recoveries)
                if recoveries
                else 0.0
            ),
            "utilization": active / len(devices) if devices else 0.0,
        }

    def dashboard(self, scope: DeviceScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "sections": [
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
            ],
            "devices": [
                serialize(item) for item in self._scope_values(self.devices, scope)
            ],
            "groups": [
                serialize(item) for item in self._scope_values(self.groups, scope)
            ],
            "profiles": [
                serialize(item) for item in self._scope_values(self.profiles, scope)
            ],
            "queues": {
                "device_queue": len(self._queue),
                "priority_queue": sum(item.priority > 0 for item in self._queue),
                "workspace_queue": len(
                    {(item.tenant, item.workspace) for item in self._queue}
                ),
                "retry_queue": sum(item.attempts > 0 for item in self._queue),
                "delayed_queue": sum(
                    item.available_at > datetime.now(timezone.utc)
                    for item in self._queue
                ),
                "maximum_concurrent_devices": (
                    self.allocation_policy.maximum_concurrent_devices
                ),
            },
            "resources": {
                "policy": serialize(self.allocation_policy),
                "reservations": [
                    serialize(item)
                    for item in self._scope_values(self.reservations, scope)
                ],
            },
            "health": self.health(scope),
            "recovery": [
                serialize(item)
                for item in self.recoveries
                if item.device_id
                in {device.id for device in self._scope_values(self.devices, scope)}
            ],
            "telemetry": dict(self.metrics.values),
            "statistics": self.statistics(scope),
        }

    @staticmethod
    def _scope_values(values: dict[str, Any], scope: DeviceScope) -> list[Any]:
        return [
            item
            for item in values.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _refresh_metrics(self) -> None:
        self.metrics.set("tiktok_devices_total", len(self.devices))
        self.metrics.set(
            "tiktok_devices_ready",
            sum(item.status is DeviceStatus.READY for item in self.devices.values()),
        )
        self.metrics.set(
            "tiktok_devices_running",
            sum(
                item.status in {DeviceStatus.RUNNING, DeviceStatus.BUSY}
                for item in self.devices.values()
            ),
        )
        self.metrics.set(
            "tiktok_devices_offline",
            sum(item.status is DeviceStatus.OFFLINE for item in self.devices.values()),
        )
        snapshots = list(self.health_snapshots.values())
        self.metrics.set(
            "tiktok_device_health_score",
            sum(item.score for item in snapshots) / len(snapshots)
            if snapshots
            else 100.0,
        )
        self.metrics.set(
            "tiktok_device_cpu_usage",
            sum(item.cpu for item in snapshots) / len(snapshots)
            if snapshots
            else 0.0,
        )
        self.metrics.set(
            "tiktok_device_memory_usage",
            sum(item.memory for item in snapshots) / len(snapshots)
            if snapshots
            else 0.0,
        )
