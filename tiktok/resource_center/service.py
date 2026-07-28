"""Enterprise TikTok Resource Center orchestration service."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any
from uuid import uuid4

from .adapters import INTEGRATION_NAMES, EmptyInventoryPort, InventoryPort
from .metrics import ResourceMetrics
from .models import (
    Allocation,
    HealthState,
    Lease,
    Priority,
    Quota,
    Reservation,
    Resource,
    ResourceScope,
    ResourceStatus,
    ResourceType,
    UtilizationSample,
    utcnow,
)

TRANSITIONS: dict[ResourceStatus, frozenset[ResourceStatus]] = {
    ResourceStatus.DISCOVERED: frozenset(
        {ResourceStatus.REGISTERED, ResourceStatus.ARCHIVED, ResourceStatus.DELETED}
    ),
    ResourceStatus.REGISTERED: frozenset(
        {
            ResourceStatus.RESERVED,
            ResourceStatus.ALLOCATED,
            ResourceStatus.IDLE,
            ResourceStatus.PAUSED,
            ResourceStatus.ARCHIVED,
        }
    ),
    ResourceStatus.RESERVED: frozenset(
        {
            ResourceStatus.ALLOCATED,
            ResourceStatus.RELEASED,
            ResourceStatus.RECOVERING,
        }
    ),
    ResourceStatus.ALLOCATED: frozenset(
        {
            ResourceStatus.RUNNING,
            ResourceStatus.IDLE,
            ResourceStatus.PAUSED,
            ResourceStatus.RECOVERING,
            ResourceStatus.RELEASED,
        }
    ),
    ResourceStatus.RUNNING: frozenset(
        {
            ResourceStatus.IDLE,
            ResourceStatus.PAUSED,
            ResourceStatus.RECOVERING,
            ResourceStatus.RELEASED,
        }
    ),
    ResourceStatus.IDLE: frozenset(
        {
            ResourceStatus.ALLOCATED,
            ResourceStatus.RUNNING,
            ResourceStatus.PAUSED,
            ResourceStatus.RECOVERING,
            ResourceStatus.RELEASED,
            ResourceStatus.ARCHIVED,
        }
    ),
    ResourceStatus.PAUSED: frozenset(
        {
            ResourceStatus.IDLE,
            ResourceStatus.RECOVERING,
            ResourceStatus.RELEASED,
            ResourceStatus.ARCHIVED,
        }
    ),
    ResourceStatus.RECOVERING: frozenset(
        {ResourceStatus.IDLE, ResourceStatus.PAUSED, ResourceStatus.RELEASED}
    ),
    ResourceStatus.RELEASED: frozenset(
        {ResourceStatus.REGISTERED, ResourceStatus.IDLE, ResourceStatus.ARCHIVED}
    ),
    ResourceStatus.ARCHIVED: frozenset(
        {ResourceStatus.REGISTERED, ResourceStatus.DELETED}
    ),
    ResourceStatus.DELETED: frozenset(),
}


class TikTokResourceCenter:
    """Tenant-isolated local inventory, allocation, and recovery coordinator."""

    def __init__(
        self,
        ports: dict[str, InventoryPort] | None = None,
        default_quota: Quota | None = None,
    ) -> None:
        supplied = ports or {}
        unknown = set(supplied) - INTEGRATION_NAMES
        if unknown:
            raise ValueError(
                f"Unknown bounded Resource Center ports: {sorted(unknown)}"
            )
        self.ports: dict[str, InventoryPort] = {
            name: supplied.get(name, EmptyInventoryPort())
            for name in INTEGRATION_NAMES
        }
        self.resources: dict[str, Resource] = {}
        self.reservations: dict[str, Reservation] = {}
        self.allocations: dict[str, Allocation] = {}
        self.leases: dict[str, Lease] = {}
        self.quotas: dict[tuple[str, str], Quota] = {}
        self.default_quota = default_quota or Quota()
        self.default_quota.validate()
        self.utilization_samples: list[UtilizationSample] = []
        self.audit: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.recovery_attempts: Counter[str] = Counter()
        self.activity: Counter[str] = Counter()
        self.metrics = ResourceMetrics()

    @staticmethod
    def _require(scope: ResourceScope, action: str) -> None:
        permission = f"tiktok:resources:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:resources:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: ResourceScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self, scope: ResourceScope, action: str, resource: str, detail: str = ""
    ) -> None:
        lowered = detail.casefold()
        if any(
            marker in lowered
            for marker in ("password=", "secret=", "token=", "cookie=", "session=")
        ):
            raise ValueError("Secrets are forbidden in Resource Center audit records.")
        self.audit.append(
            {
                "actor": scope.actor,
                "action": action,
                "resource": resource,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "detail": detail,
                "timestamp": utcnow(),
            }
        )
        self.activity[action] += 1

    def scoped_values(self, values: Any, scope: ResourceScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def quota_for(self, scope: ResourceScope) -> Quota:
        return self.quotas.get((scope.tenant, scope.workspace), self.default_quota)

    def set_quota(self, quota: Quota, scope: ResourceScope) -> Quota:
        self._require(scope, "admin")
        quota.validate()
        self.quotas[(scope.tenant, scope.workspace)] = quota
        self._record(scope, "quota.updated", scope.workspace)
        return quota

    def register(self, resource: Resource, scope: ResourceScope) -> Resource:
        self._require(scope, "write")
        self._scoped(resource, scope)
        resource.validate()
        if resource.id in self.resources:
            raise ValueError("Resource ID must be unique.")
        if len(self.scoped_values(self.resources.values(), scope)) >= self.quota_for(
            scope
        ).workspace:
            raise OverflowError("Workspace resource quota reached.")
        type_limit = self._quota_limit(resource.resource_type, self.quota_for(scope))
        same_type = sum(
            item.resource_type is resource.resource_type
            for item in self.scoped_values(self.resources.values(), scope)
        )
        if type_limit is not None and same_type >= type_limit:
            raise OverflowError(f"{resource.resource_type.value} quota reached.")
        if resource.status is ResourceStatus.DISCOVERED:
            resource.status = ResourceStatus.REGISTERED
        self.resources[resource.id] = resource
        self.metrics.increment("tiktok_resources_total")
        self.metrics.increment(
            "tiktok_resource_capacity_total", resource.maximum_capacity
        )
        self._record(
            scope, "resource.registered", resource.id, resource.resource_type.value
        )
        return resource

    @staticmethod
    def _quota_limit(resource_type: ResourceType, quota: Quota) -> int | None:
        return {
            ResourceType.ACCOUNT: quota.account,
            ResourceType.BROWSER: quota.browser,
            ResourceType.BROWSER_CLUSTER_NODE: quota.browser,
            ResourceType.DEVICE: quota.device,
            ResourceType.PROXY: quota.proxy,
            ResourceType.WORKER: quota.worker,
            ResourceType.QUEUE: quota.task,
        }.get(resource_type)

    def discover(self, scope: ResourceScope) -> list[Resource]:
        self._require(scope, "discover")
        discovered: list[Resource] = []
        for name, port in self.ports.items():
            for resource in port.discover(scope):
                self._scoped(resource, scope)
                resource.validate()
                if resource.id in self.resources:
                    continue
                resource.status = ResourceStatus.DISCOVERED
                resource.metadata = {**resource.metadata, "source": name}
                self.resources[resource.id] = resource
                discovered.append(resource)
                self.metrics.increment("tiktok_resources_total")
                self.metrics.increment(
                    "tiktok_resource_capacity_total", resource.maximum_capacity
                )
        self._record(scope, "inventory.discovered", "*", str(len(discovered)))
        return discovered

    def search(
        self,
        scope: ResourceScope,
        *,
        query: str = "",
        resource_type: ResourceType | None = None,
        status: ResourceStatus | None = None,
        tags: frozenset[str] = frozenset(),
        group: str = "",
    ) -> list[Resource]:
        self._require(scope, "read")
        needle = query.casefold()
        return [
            item
            for item in self.scoped_values(self.resources.values(), scope)
            if (
                not needle
                or needle in item.id.casefold()
                or needle in item.name.casefold()
            )
            and (resource_type is None or item.resource_type is resource_type)
            and (status is None or item.status is status)
            and (not tags or tags <= item.tags)
            and (not group or item.group == group)
        ]

    def transition(
        self, resource_id: str, status: ResourceStatus, scope: ResourceScope
    ) -> Resource:
        self._require(scope, "write")
        resource = self.resources[resource_id]
        self._scoped(resource, scope)
        if status not in TRANSITIONS[resource.status]:
            raise ValueError(
                "Invalid resource transition: "
                f"{resource.status.value} -> {status.value}"
            )
        resource.status = status
        resource.version += 1
        resource.updated_at = utcnow()
        self._record(scope, "resource.transitioned", resource_id, status.value)
        return resource

    def reserve(
        self,
        resource_id: str,
        owner: str,
        scope: ResourceScope,
        *,
        duration_seconds: int = 300,
        priority: Priority = Priority.NORMAL,
    ) -> Reservation:
        self._require(scope, "allocate")
        resource = self.resources[resource_id]
        self._scoped(resource, scope)
        self.cleanup_expired(scope)
        if not 1 <= duration_seconds <= 86_400:
            raise ValueError("Reservation duration must be within [1, 86400].")
        if resource.status not in {
            ResourceStatus.REGISTERED,
            ResourceStatus.IDLE,
            ResourceStatus.RELEASED,
        }:
            raise RuntimeError("Resource has a reservation or allocation conflict.")
        now = utcnow()
        reservation = Reservation(
            f"reservation-{uuid4().hex}",
            resource_id,
            scope.tenant,
            scope.workspace,
            owner,
            now,
            now + timedelta(seconds=duration_seconds),
            priority,
            now,
        )
        self.reservations[reservation.id] = reservation
        if resource.status is ResourceStatus.RELEASED:
            self.transition(resource_id, ResourceStatus.REGISTERED, scope)
        self.transition(resource_id, ResourceStatus.RESERVED, scope)
        self.metrics.increment("tiktok_resource_reservations_total")
        self._record(scope, "reservation.created", reservation.id, resource_id)
        return reservation

    def heartbeat_reservation(
        self, reservation_id: str, scope: ResourceScope, renewal_seconds: int = 300
    ) -> Reservation:
        self._require(scope, "allocate")
        reservation = self.reservations[reservation_id]
        self._scoped(reservation, scope)
        if reservation.cancelled or reservation.expires_at <= utcnow():
            raise RuntimeError("Reservation is no longer active.")
        if not 1 <= renewal_seconds <= 86_400:
            raise ValueError("Renewal duration must be within [1, 86400].")
        reservation.heartbeat_at = utcnow()
        reservation.expires_at = reservation.heartbeat_at + timedelta(
            seconds=renewal_seconds
        )
        self._record(scope, "reservation.renewed", reservation_id)
        return reservation

    def cancel_reservation(
        self, reservation_id: str, scope: ResourceScope
    ) -> Reservation:
        self._require(scope, "allocate")
        reservation = self.reservations[reservation_id]
        self._scoped(reservation, scope)
        reservation.cancelled = True
        resource = self.resources[reservation.resource_id]
        if resource.status is ResourceStatus.RESERVED:
            self.transition(resource.id, ResourceStatus.RELEASED, scope)
        self._record(scope, "reservation.cancelled", reservation_id)
        return reservation

    def allocate(
        self,
        resource_id: str,
        owner: str,
        scope: ResourceScope,
        *,
        reservation_id: str = "",
        approval_reference: str = "",
        lease_seconds: int = 900,
        priority: Priority = Priority.NORMAL,
    ) -> tuple[Allocation, Lease]:
        self._require(scope, "allocate")
        self.cleanup_expired(scope)
        resource = self.resources[resource_id]
        self._scoped(resource, scope)
        if resource.restriction_active or resource.challenge_active:
            raise RuntimeError(
                "Unresolved TikTok restriction or challenge blocks allocation."
            )
        if resource.metadata.get("requires_approval") and not approval_reference:
            raise PermissionError("An approval reference is required for allocation.")
        if approval_reference and not approval_reference.startswith("approval://"):
            raise ValueError("Approval must be supplied as an opaque reference.")
        if any(
            allocation.resource_id == resource_id
            and allocation.cooldown_until is not None
            and allocation.cooldown_until > utcnow()
            for allocation in self.allocations.values()
        ):
            raise RuntimeError("Resource allocation cooldown is active.")
        if resource.status is ResourceStatus.RESERVED:
            if not reservation_id:
                raise RuntimeError("A matching active reservation is required.")
            reservation = self.reservations[reservation_id]
            self._scoped(reservation, scope)
            if (
                reservation.resource_id != resource_id
                or reservation.owner != owner
                or reservation.cancelled
                or reservation.expires_at <= utcnow()
            ):
                raise RuntimeError("Reservation ownership validation failed.")
            reservation.cancelled = True
        elif resource.status not in {
            ResourceStatus.REGISTERED,
            ResourceStatus.IDLE,
            ResourceStatus.RELEASED,
        }:
            raise RuntimeError("Resource is not available for allocation.")
        if not 1 <= lease_seconds <= 604_800:
            raise ValueError("Lease duration must be within [1, 604800].")
        now = utcnow()
        allocation = Allocation(
            f"allocation-{uuid4().hex}",
            resource_id,
            scope.tenant,
            scope.workspace,
            owner,
            priority,
            now,
            reservation_id,
        )
        lease = Lease(
            f"lease-{uuid4().hex}",
            allocation.id,
            resource_id,
            scope.tenant,
            scope.workspace,
            owner,
            now,
            now + timedelta(seconds=lease_seconds),
            now,
        )
        self.allocations[allocation.id] = allocation
        self.leases[lease.id] = lease
        if resource.status is ResourceStatus.RELEASED:
            self.transition(resource.id, ResourceStatus.REGISTERED, scope)
        self.transition(resource.id, ResourceStatus.ALLOCATED, scope)
        self.metrics.increment("tiktok_resource_allocations_total")
        self.metrics.increment("tiktok_resource_leases_total")
        self._record(scope, "allocation.created", allocation.id, resource_id)
        return allocation, lease

    def renew_lease(
        self,
        lease_id: str,
        owner: str,
        scope: ResourceScope,
        duration_seconds: int = 900,
    ) -> Lease:
        self._require(scope, "allocate")
        lease = self.leases[lease_id]
        self._scoped(lease, scope)
        if not lease.active or lease.expires_at <= utcnow() or lease.owner != owner:
            raise RuntimeError("Lease ownership or activity validation failed.")
        if not 1 <= duration_seconds <= 604_800:
            raise ValueError("Lease duration must be within [1, 604800].")
        lease.renewed_at = utcnow()
        lease.expires_at = lease.renewed_at + timedelta(seconds=duration_seconds)
        self._record(scope, "lease.renewed", lease_id)
        return lease

    def release(
        self,
        allocation_id: str,
        owner: str,
        scope: ResourceScope,
        cooldown_seconds: int = 0,
    ) -> Allocation:
        self._require(scope, "allocate")
        allocation = self.allocations[allocation_id]
        self._scoped(allocation, scope)
        if allocation.owner != owner:
            raise PermissionError("Allocation ownership validation failed.")
        if not 0 <= cooldown_seconds <= 86_400:
            raise ValueError("Cooldown must be within [0, 86400].")
        now = utcnow()
        allocation.released_at = now
        allocation.cooldown_until = now + timedelta(seconds=cooldown_seconds)
        for lease in self.leases.values():
            if lease.allocation_id == allocation_id:
                lease.active = False
        resource = self.resources[allocation.resource_id]
        if resource.status not in {ResourceStatus.RELEASED, ResourceStatus.ARCHIVED}:
            self.transition(resource.id, ResourceStatus.RELEASED, scope)
        self._record(scope, "allocation.released", allocation_id)
        return allocation

    def cleanup_expired(self, scope: ResourceScope) -> dict[str, int]:
        self._require(scope, "allocate")
        now = utcnow()
        reservations = 0
        leases = 0
        for reservation in self.scoped_values(self.reservations.values(), scope):
            if not reservation.cancelled and reservation.expires_at <= now:
                reservation.cancelled = True
                resource = self.resources[reservation.resource_id]
                if resource.status is ResourceStatus.RESERVED:
                    self.transition(resource.id, ResourceStatus.RELEASED, scope)
                reservations += 1
        for lease in self.scoped_values(self.leases.values(), scope):
            if lease.active and lease.expires_at <= now:
                lease.active = False
                allocation = self.allocations[lease.allocation_id]
                if allocation.released_at is None:
                    allocation.released_at = now
                resource = self.resources[lease.resource_id]
                if resource.status not in {
                    ResourceStatus.RELEASED,
                    ResourceStatus.ARCHIVED,
                    ResourceStatus.DELETED,
                }:
                    self.transition(resource.id, ResourceStatus.RELEASED, scope)
                leases += 1
        if reservations or leases:
            self._record(
                scope, "expiration.cleaned", "*", f"{reservations}:{leases}"
            )
        return {"reservations": reservations, "leases": leases}

    def record_utilization(
        self, sample: UtilizationSample, scope: ResourceScope
    ) -> UtilizationSample:
        self._require(scope, "monitor")
        self._scoped(sample, scope)
        sample.validate()
        self.utilization_samples.append(sample)
        self.metrics.set("tiktok_resource_utilization_ratio", sample.ratio)
        self._record(scope, "utilization.recorded", scope.workspace)
        return sample

    def capacity(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        resources = self.scoped_values(self.resources.values(), scope)
        maximum = sum(item.maximum_capacity for item in resources)
        reserved = sum(
            self.resources[item.resource_id].maximum_capacity
            for item in self.scoped_values(self.reservations.values(), scope)
            if not item.cancelled and item.expires_at > utcnow()
        )
        allocated_ids = {
            item.resource_id
            for item in self.scoped_values(self.allocations.values(), scope)
            if item.released_at is None
        }
        allocated = sum(
            item.maximum_capacity for item in resources if item.id in allocated_ids
        )
        unavailable = {
            item.resource_id
            for item in self.scoped_values(self.reservations.values(), scope)
            if not item.cancelled and item.expires_at > utcnow()
        } | allocated_ids
        available = sum(
            item.maximum_capacity
            for item in resources
            if item.id not in unavailable
            and item.status
            not in {
                ResourceStatus.ARCHIVED,
                ResourceStatus.DELETED,
                ResourceStatus.PAUSED,
            }
        )
        remaining = max(0.0, maximum - reserved - allocated)
        ratio = (allocated + reserved) / maximum if maximum else 0.0
        recommendation = (
            "scale_up"
            if ratio >= 0.8
            else "review_capacity"
            if ratio >= 0.6
            else "stable"
        )
        return {
            "maximum_capacity": maximum,
            "available_capacity": available,
            "reserved_capacity": reserved,
            "allocated_capacity": allocated,
            "remaining_capacity": remaining,
            "scaling_recommendation": recommendation,
        }

    def utilization(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        samples = self.scoped_values(self.utilization_samples, scope)
        if not samples:
            return {"current": {}, "trend": [], "utilization_rate": 0.0}
        current = samples[-1]
        return {
            "current": {
                name: getattr(current, name)
                for name in (
                    "cpu",
                    "memory",
                    "browser_slots",
                    "devices",
                    "workers",
                    "queue_usage",
                    "proxy_usage",
                    "account_usage",
                )
            },
            "trend": [
                {"captured_at": item.captured_at, "ratio": item.ratio}
                for item in samples[-100:]
            ],
            "utilization_rate": current.ratio,
        }

    def health(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        resources = self.scoped_values(self.resources.values(), scope)
        scores = {
            HealthState.HEALTHY: 100.0,
            HealthState.DEGRADED: 60.0,
            HealthState.UNKNOWN: 50.0,
            HealthState.UNHEALTHY: 0.0,
        }
        inventory = (
            sum(scores[item.health] for item in resources) / len(resources)
            if resources
            else 100.0
        )
        active_allocations = [
            item
            for item in self.scoped_values(self.allocations.values(), scope)
            if item.released_at is None
        ]
        active_leases = [
            item
            for item in self.scoped_values(self.leases.values(), scope)
            if item.active
        ]
        active_reservations = [
            item
            for item in self.scoped_values(self.reservations.values(), scope)
            if not item.cancelled
        ]
        allocation = 100.0 if all(
            item.resource_id in self.resources for item in active_allocations
        ) else 0.0
        lease = (
            100.0
            if all(item.expires_at > utcnow() for item in active_leases)
            else 50.0
        )
        reservation = (
            100.0
            if all(item.expires_at > utcnow() for item in active_reservations)
            else 50.0
        )
        capacity = 100.0 if self.capacity(scope)["remaining_capacity"] >= 0 else 0.0
        utilization = max(
            0.0, 100.0 - self.utilization(scope)["utilization_rate"] * 30.0
        )
        composite = sum(
            (inventory, allocation, lease, reservation, capacity, utilization)
        ) / 6
        self.metrics.set("tiktok_resource_health_score", composite)
        return {
            "inventory_health": inventory,
            "allocation_health": allocation,
            "lease_health": lease,
            "reservation_health": reservation,
            "capacity_health": capacity,
            "utilization_health": utilization,
            "composite_health_score": composite,
        }

    def recover(
        self,
        resource_id: str,
        scope: ResourceScope,
        *,
        maximum_attempts: int = 3,
        backoff_seconds: int = 5,
        cooldown_seconds: int = 30,
    ) -> Resource:
        self._require(scope, "recover")
        resource = self.resources[resource_id]
        self._scoped(resource, scope)
        if resource.restriction_active or resource.challenge_active:
            self.failures.append(
                {
                    "resource_id": resource_id,
                    "reason": "unresolved_tiktok_restriction_or_challenge",
                    "tenant": scope.tenant,
                    "workspace": scope.workspace,
                    "timestamp": utcnow(),
                }
            )
            raise RuntimeError(
                "Recovery stopped for unresolved TikTok restriction or challenge."
            )
        if not 1 <= maximum_attempts <= 10:
            raise ValueError("Recovery attempts must be within [1, 10].")
        if not 0 <= backoff_seconds <= 3600 or not 0 <= cooldown_seconds <= 86_400:
            raise ValueError("Recovery backoff or cooldown is outside bounded limits.")
        if resource.status is not ResourceStatus.RECOVERING:
            self.transition(resource_id, ResourceStatus.RECOVERING, scope)
        self.recovery_attempts[resource_id] += 1
        if self.recovery_attempts[resource_id] > maximum_attempts:
            self.transition(resource_id, ResourceStatus.PAUSED, scope)
            raise RuntimeError("Bounded recovery attempts exhausted.")
        resource.health = HealthState.HEALTHY
        self.transition(resource_id, ResourceStatus.IDLE, scope)
        self.metrics.increment("tiktok_resource_recovery_total")
        self._record(
            scope,
            "resource.recovered",
            resource_id,
            f"backoff={backoff_seconds};cooldown={cooldown_seconds}",
        )
        return resource

    def reconcile(self, scope: ResourceScope) -> dict[str, int]:
        self._require(scope, "recover")
        cleaned = self.cleanup_expired(scope)
        discovered = len(self.discover(scope))
        self._record(scope, "inventory.reconciled", "*")
        return {**cleaned, "discovered": discovered}

    def telemetry(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        resources = self.scoped_values(self.resources.values(), scope)
        allocations = self.scoped_values(self.allocations.values(), scope)
        reservations = self.scoped_values(self.reservations.values(), scope)
        leases = self.scoped_values(self.leases.values(), scope)
        return {
            "inventory_size": len(resources),
            "allocation_count": len(allocations),
            "reservation_count": len(reservations),
            "lease_count": len(leases),
            "utilization": self.utilization(scope),
            "health": self.health(scope),
            "failures": len(
                [
                    item
                    for item in self.failures
                    if item["tenant"] == scope.tenant
                    and item["workspace"] == scope.workspace
                ]
            ),
            "recovery": sum(
                self.recovery_attempts[item.id] for item in resources
            ),
        }

    def statistics(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        resources = self.scoped_values(self.resources.values(), scope)
        allocations = self.scoped_values(self.allocations.values(), scope)
        reservations = self.scoped_values(self.reservations.values(), scope)
        recovered = sum(
            self.recovery_attempts[item.id] > 0 and item.health is HealthState.HEALTHY
            for item in resources
        )
        attempts = sum(self.recovery_attempts[item.id] for item in resources)
        return {
            "allocation_rate": len(allocations) / len(resources) if resources else 0.0,
            "release_rate": (
                sum(item.released_at is not None for item in allocations)
                / len(allocations)
                if allocations
                else 0.0
            ),
            "reservation_rate": (
                len(reservations) / len(resources) if resources else 0.0
            ),
            "utilization_rate": self.utilization(scope)["utilization_rate"],
            "capacity_trend": self.capacity(scope),
            "health_trend": self.health(scope)["composite_health_score"],
            "recovery_success": recovered / attempts if attempts else 1.0,
        }

    def dashboard(self, scope: ResourceScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "overview": self.telemetry(scope),
            "inventory": [
                {
                    "id": item.id,
                    "name": item.name,
                    "type": item.resource_type.value,
                    "status": item.status.value,
                    "version": item.version,
                }
                for item in self.scoped_values(self.resources.values(), scope)
            ],
            "allocations": len(self.scoped_values(self.allocations.values(), scope)),
            "reservations": len(self.scoped_values(self.reservations.values(), scope)),
            "leases": len(self.scoped_values(self.leases.values(), scope)),
            "capacity": self.capacity(scope),
            "utilization": self.utilization(scope),
            "health": self.health(scope),
            "recovery": {
                item.id: self.recovery_attempts[item.id]
                for item in self.scoped_values(self.resources.values(), scope)
            },
            "statistics": self.statistics(scope),
            "safety": {
                "local_single_user": True,
                "bounded_interfaces": True,
                "captcha_bypass": False,
                "restriction_bypass": False,
            },
        }
