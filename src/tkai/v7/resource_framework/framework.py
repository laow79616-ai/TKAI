"""Advisory, metadata-only V7 Unified Resource Management Framework."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from tkai.v7.security import AccessController, Principal, filter_secrets

from .contracts import (
    AllocationPlan,
    AuditEntry,
    CapacityAnalysis,
    RecoveryPlan,
    Reservation,
    ReservationConflict,
    Resource,
    ResourceLifecycle,
    ResourceType,
    ResourceTypeContract,
    ValidationIssue,
    ValidationReport,
    serialize,
    utc_now,
)

LIFECYCLE_TRANSITIONS: Mapping[
    ResourceLifecycle, frozenset[ResourceLifecycle]
] = {
    ResourceLifecycle.REGISTERED: frozenset(
        {
            ResourceLifecycle.VALIDATED,
            ResourceLifecycle.UNAVAILABLE,
            ResourceLifecycle.ARCHIVED,
        }
    ),
    ResourceLifecycle.VALIDATED: frozenset(
        {
            ResourceLifecycle.AVAILABLE,
            ResourceLifecycle.UNAVAILABLE,
            ResourceLifecycle.PAUSED,
        }
    ),
    ResourceLifecycle.AVAILABLE: frozenset(
        {
            ResourceLifecycle.RESERVED,
            ResourceLifecycle.PLANNED,
            ResourceLifecycle.UNAVAILABLE,
            ResourceLifecycle.PAUSED,
        }
    ),
    ResourceLifecycle.RESERVED: frozenset(
        {
            ResourceLifecycle.AVAILABLE,
            ResourceLifecycle.PLANNED,
            ResourceLifecycle.UNAVAILABLE,
        }
    ),
    ResourceLifecycle.PLANNED: frozenset(
        {
            ResourceLifecycle.AVAILABLE,
            ResourceLifecycle.RESERVED,
            ResourceLifecycle.PAUSED,
            ResourceLifecycle.UNAVAILABLE,
        }
    ),
    ResourceLifecycle.UNAVAILABLE: frozenset(
        {
            ResourceLifecycle.RECOVERING,
            ResourceLifecycle.PAUSED,
            ResourceLifecycle.ARCHIVED,
        }
    ),
    ResourceLifecycle.PAUSED: frozenset(
        {
            ResourceLifecycle.AVAILABLE,
            ResourceLifecycle.UNAVAILABLE,
            ResourceLifecycle.ARCHIVED,
        }
    ),
    ResourceLifecycle.RECOVERING: frozenset(
        {
            ResourceLifecycle.AVAILABLE,
            ResourceLifecycle.UNAVAILABLE,
            ResourceLifecycle.PAUSED,
        }
    ),
    ResourceLifecycle.ARCHIVED: frozenset({ResourceLifecycle.DELETED}),
    ResourceLifecycle.DELETED: frozenset(),
}

METRIC_NAMES = (
    "v7_resource_registered_total",
    "v7_resource_validations_total",
    "v7_resource_validation_failures_total",
    "v7_resource_plans_total",
    "v7_resource_plan_conflicts_total",
    "v7_resource_reservations_total",
    "v7_resource_reservation_conflicts_total",
    "v7_resource_transitions_total",
    "v7_resource_recoveries_total",
    "v7_resource_discoveries_total",
)


class ResourceFrameworkError(RuntimeError):
    pass


class ResourceValidationError(ResourceFrameworkError):
    pass


class DependencyCycleError(ResourceValidationError):
    pass


class ReservationConflictError(ResourceValidationError):
    def __init__(self, conflict: ReservationConflict) -> None:
        self.conflict = conflict
        super().__init__(
            f"resource {conflict.resource_id!r} has {conflict.available} available; "
            f"{conflict.requested} requested"
        )


class IllegalLifecycleTransition(ResourceFrameworkError):
    pass


class ResourceRegistry:
    def __init__(self) -> None:
        self._resources: dict[str, Resource] = {}
        self._lock = RLock()

    def register(self, resource: Resource) -> Resource:
        with self._lock:
            if resource.resource_id in self._resources:
                raise ResourceValidationError(
                    f"resource already registered: {resource.resource_id}"
                )
            self._resources[resource.resource_id] = resource
            return resource

    def get(self, resource_id: str) -> Resource:
        try:
            return self._resources[resource_id]
        except KeyError as error:
            raise KeyError(f"unknown resource: {resource_id}") from error

    def replace(self, resource: Resource) -> Resource:
        with self._lock:
            if resource.resource_id not in self._resources:
                raise KeyError(f"unknown resource: {resource.resource_id}")
            self._resources[resource.resource_id] = resource
            return resource

    def list(self) -> tuple[Resource, ...]:
        return tuple(self._resources[key] for key in sorted(self._resources))


class ResourceCatalog:
    def __init__(self) -> None:
        self._contracts: dict[str, ResourceTypeContract] = {}
        for resource_type in ResourceType:
            self.register_type(ResourceTypeContract(resource_type.value))

    def register_type(self, contract: ResourceTypeContract) -> None:
        key = contract.name.strip().lower().replace(" ", "_")
        if key in self._contracts:
            raise ResourceValidationError(f"resource type already exists: {key}")
        self._contracts[key] = replace(contract, name=key)

    def get(self, name: str) -> ResourceTypeContract:
        try:
            return self._contracts[name.strip().lower().replace(" ", "_")]
        except KeyError as error:
            raise KeyError(f"unknown resource type: {name}") from error

    def list(self) -> tuple[ResourceTypeContract, ...]:
        return tuple(self._contracts[key] for key in sorted(self._contracts))


class ResourceSecurity:
    def __init__(self, access: AccessController | None = None) -> None:
        self.access = access

    def authorize(
        self,
        resource: Resource,
        capability: str,
        *,
        principal: Principal | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
        owner: str | None = None,
    ) -> None:
        if self.access is not None:
            if principal is None:
                raise PermissionError("principal required")
            self.access.require(principal, capability)
        if tenant_reference and resource.scope.tenant_reference != tenant_reference:
            raise PermissionError("tenant isolation violation")
        if workspace_reference and (
            resource.scope.workspace_reference != workspace_reference
        ):
            raise PermissionError("workspace isolation violation")
        if owner and resource.owner != owner:
            raise PermissionError("resource isolation violation")


class Metrics:
    def __init__(self) -> None:
        self._values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str) -> None:
        self._values[name] += 1

    def snapshot(self) -> dict[str, float]:
        return dict(self._values)


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(self, hook: Callable[[str, Mapping[str, object]], None]) -> None:
        self._hooks.append(hook)

    def emit(self, name: str, attributes: Mapping[str, object]) -> None:
        safe = filter_secrets(attributes)
        for hook in self._hooks:
            hook(name, safe)


class ResourceFramework:
    """Coordinates resource metadata and advice without allocating anything."""

    def __init__(
        self,
        registry: ResourceRegistry | None = None,
        *,
        catalog: ResourceCatalog | None = None,
        security: ResourceSecurity | None = None,
        max_plan_size: int = 1000,
    ) -> None:
        if max_plan_size < 1:
            raise ValueError("max_plan_size must be positive")
        self.registry = registry or ResourceRegistry()
        self.catalog = catalog or ResourceCatalog()
        self.security = security or ResourceSecurity()
        self.max_plan_size = max_plan_size
        self.metrics = Metrics()
        self.tracing = TracingHooks()
        self.reservations: list[Reservation] = []
        self.reservation_history: list[Reservation] = []
        self.plans: list[AllocationPlan] = []
        self.capacity_history: list[CapacityAnalysis] = []
        self.recoveries: list[RecoveryPlan] = []
        self.history: list[AuditEntry] = []
        self.logs: list[dict[str, object]] = []

    def _record(
        self,
        resource_id: str,
        category: str,
        action: str,
        actor: str,
        reference: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        entry = AuditEntry(
            str(uuid4()), resource_id, category, action, actor, reference, details or {}
        )
        self.history.append(entry)
        self.logs.append(
            {
                "timestamp": entry.timestamp,
                "level": "info",
                "event": f"resource.{action}",
                "resource_id": resource_id,
                "actor": actor,
                "details": filter_secrets(details or {}),
            }
        )

    def register(self, resource: Resource, *, actor: str = "system") -> Resource:
        self.catalog.get(resource.resource_type)
        result = self.registry.register(resource)
        self.metrics.increment("v7_resource_registered_total")
        self._record(resource.resource_id, "registry", "registered", actor)
        self.tracing.emit("resource.registered", {"resource_id": resource.resource_id})
        return result

    def discover(
        self,
        *,
        resource_type: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        capability: str | None = None,
        dependency_id: str | None = None,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, object] | None = None,
    ) -> tuple[Resource, ...]:
        result = self.registry.list()
        if resource_type:
            normalized = resource_type.strip().lower().replace(" ", "_")
            result = tuple(item for item in result if item.resource_type == normalized)
        if category:
            result = tuple(item for item in result if item.category == category)
        if owner:
            result = tuple(item for item in result if item.owner == owner)
        if capability:
            result = tuple(item for item in result if capability in item.capabilities)
        if dependency_id:
            result = tuple(
                item
                for item in result
                if dependency_id
                in {dependency.resource_id for dependency in item.dependency_references}
            )
        if tags:
            result = tuple(item for item in result if tags <= item.tags)
        if metadata:
            result = tuple(
                item
                for item in result
                if all(
                    item.metadata.get(key) == value for key, value in metadata.items()
                )
            )
        self.metrics.increment("v7_resource_discoveries_total")
        return result

    def validate(self, resource_id: str, *, actor: str = "system") -> ValidationReport:
        resource = self.registry.get(resource_id)
        issues: list[ValidationIssue] = []
        if not re.fullmatch(
            r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", resource.version
        ):
            issues.append(
                ValidationIssue(
                    "version_invalid", "version must be semantic", resource_id
                )
            )
        capacity = resource.capacity
        if (
            capacity.total < 0
            or capacity.used < 0
            or capacity.reserved < 0
            or capacity.used + capacity.reserved > capacity.total
        ):
            issues.append(
                ValidationIssue(
                    "capacity_invalid", "capacity values are inconsistent", resource_id
                )
            )
        known = {item.resource_id: item for item in self.registry.list()}
        for dependency in resource.dependency_references:
            target = known.get(dependency.resource_id)
            if target is None and not dependency.optional:
                issues.append(
                    ValidationIssue(
                        "dependency_missing",
                        f"dependency is not registered: {dependency.resource_id}",
                        resource_id,
                    )
                )
            elif (
                target
                and dependency.required_version
                and target.version != dependency.required_version
            ):
                issues.append(
                    ValidationIssue(
                        "dependency_version_mismatch",
                        f"dependency version mismatch: {dependency.resource_id}",
                        resource_id,
                    )
                )
            if target and target.scope != resource.scope:
                issues.append(
                    ValidationIssue(
                        "dependency_isolation_violation",
                        f"dependency crosses resource scope: {dependency.resource_id}",
                        resource_id,
                    )
                )
        for constraint in resource.constraints:
            if not constraint.satisfied:
                issues.append(
                    ValidationIssue(
                        "constraint_unsatisfied", constraint.name, resource_id
                    )
                )
        try:
            self._ordered_dependencies(resource_id)
        except DependencyCycleError as error:
            issues.append(ValidationIssue("dependency_cycle", str(error), resource_id))
        report = ValidationReport(resource_id, not issues, tuple(issues))
        self.metrics.increment("v7_resource_validations_total")
        if issues:
            self.metrics.increment("v7_resource_validation_failures_total")
        self._record(
            resource_id,
            "validation",
            "validated",
            actor,
            details={"valid": report.valid, "issues": len(issues)},
        )
        return report

    def _ordered_dependencies(self, resource_id: str) -> tuple[str, ...]:
        ordered: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(item_id: str) -> None:
            if item_id in visiting:
                raise DependencyCycleError(f"dependency cycle at {item_id}")
            if item_id in visited:
                return
            visiting.add(item_id)
            item = self.registry.get(item_id)
            for dependency in sorted(
                item.dependency_references, key=lambda value: value.resource_id
            ):
                try:
                    self.registry.get(dependency.resource_id)
                except KeyError:
                    if dependency.optional:
                        continue
                    raise
                visit(dependency.resource_id)
            visiting.remove(item_id)
            visited.add(item_id)
            ordered.append(item_id)

        visit(resource_id)
        return tuple(ordered)

    def analyze_capacity(
        self,
        resource_id: str,
        *,
        growth_rate: float = 0.0,
        historical_trend_references: tuple[str, ...] = (),
    ) -> CapacityAnalysis:
        resource = self.registry.get(resource_id)
        capacity = resource.capacity
        active = sum(
            reservation.quantity
            for reservation in self.active_reservations(resource_id)
        )
        available = max(
            0.0, capacity.total - capacity.used - capacity.reserved - active
        )
        analysis = CapacityAnalysis(
            resource_id,
            capacity.total,
            capacity.used,
            capacity.reserved + active,
            available,
            capacity.utilization,
            0.0 if capacity.total <= 0 else available / capacity.total,
            0.0 if capacity.total <= 0 else active / capacity.total,
            max(0.0, capacity.total * growth_rate),
            historical_trend_references,
        )
        self.capacity_history.append(analysis)
        return analysis

    def active_reservations(self, resource_id: str) -> tuple[Reservation, ...]:
        now = datetime.now(timezone.utc)
        active: list[Reservation] = []
        for reservation in self.reservations:
            if reservation.resource_id != resource_id or reservation.status != "active":
                continue
            if reservation.expires_at:
                expiry = datetime.fromisoformat(reservation.expires_at)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                if expiry <= now:
                    continue
            active.append(reservation)
        return tuple(active)

    def reserve(
        self,
        resource_id: str,
        quantity: float,
        owner: str,
        *,
        expires_at: str | None = None,
        reference: str | None = None,
        actor: str = "system",
    ) -> Reservation:
        resource = self.registry.get(resource_id)
        if quantity <= 0:
            raise ResourceValidationError("reservation quantity must be positive")
        if reference is not None and "://" not in reference:
            raise ResourceValidationError("reservation must use a reference")
        available = self.analyze_capacity(resource_id).available
        if quantity > available:
            conflict = ReservationConflict(
                resource_id,
                quantity,
                available,
                tuple(
                    item.reservation_id
                    for item in self.active_reservations(resource_id)
                ),
            )
            self.metrics.increment("v7_resource_reservation_conflicts_total")
            raise ReservationConflictError(conflict)
        reservation = Reservation(
            str(uuid4()),
            resource_id,
            quantity,
            owner,
            resource.scope,
            expires_at,
            reference,
        )
        self.reservations.append(reservation)
        self.reservation_history.append(reservation)
        self.metrics.increment("v7_resource_reservations_total")
        self._record(
            resource_id,
            "reservation",
            "reserved",
            actor,
            reservation.reservation_id,
            {"quantity": quantity, "reference_only": True},
        )
        return reservation

    def expire_reservation(
        self, reservation_id: str, *, actor: str = "system"
    ) -> Reservation:
        for index, reservation in enumerate(self.reservations):
            if reservation.reservation_id == reservation_id:
                expired = replace(reservation, status="expired")
                self.reservations[index] = expired
                self.reservation_history.append(expired)
                self._record(
                    reservation.resource_id,
                    "reservation",
                    "expired",
                    actor,
                    reservation_id,
                )
                return expired
        raise KeyError(f"unknown reservation: {reservation_id}")

    def plan(
        self,
        resource_id: str,
        *,
        requested_capacity: float = 1.0,
        actor: str = "system",
    ) -> AllocationPlan:
        if requested_capacity <= 0:
            raise ResourceValidationError("requested capacity must be positive")
        report = self.validate(resource_id, actor=actor)
        conflicts = [issue.message for issue in report.issues]
        try:
            ordered = self._ordered_dependencies(resource_id)
        except (DependencyCycleError, KeyError) as error:
            ordered = ()
            conflicts.append(str(error))
        analysis = self.analyze_capacity(resource_id)
        if requested_capacity > analysis.available:
            conflicts.append("requested capacity exceeds estimated availability")
        resource = self.registry.get(resource_id)
        if not resource.availability.available:
            conflicts.append(resource.availability.reason or "resource unavailable")
        bounded = len(ordered) <= self.max_plan_size
        if not bounded:
            conflicts.append("plan exceeds resource planning bound")
        plan = AllocationPlan(
            str(uuid4()),
            resource_id,
            ordered,
            requested_capacity,
            not conflicts,
            bounded,
            tuple(conflicts),
            tuple(
                reservation.reservation_id
                for reservation in self.active_reservations(resource_id)
            ),
        )
        self.plans.append(plan)
        self.metrics.increment("v7_resource_plans_total")
        if conflicts:
            self.metrics.increment("v7_resource_plan_conflicts_total")
        self._record(
            resource_id,
            "planning",
            "planned",
            actor,
            plan.plan_id,
            {"ready": plan.ready, "advisory_only": True},
        )
        self.tracing.emit(
            "resource.planned",
            {"resource_id": resource_id, "plan_id": plan.plan_id},
        )
        return plan

    def transition(
        self,
        resource_id: str,
        lifecycle: ResourceLifecycle,
        *,
        actor: str = "system",
        principal: Principal | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
    ) -> Resource:
        resource = self.registry.get(resource_id)
        self.security.authorize(
            resource,
            "resource.transition",
            principal=principal,
            tenant_reference=tenant_reference,
            workspace_reference=workspace_reference,
        )
        if lifecycle not in LIFECYCLE_TRANSITIONS[resource.lifecycle]:
            raise IllegalLifecycleTransition(
                f"illegal transition: {resource.lifecycle.value} -> {lifecycle.value}"
            )
        updated = replace(resource, lifecycle=lifecycle, updated_at=utc_now())
        self.registry.replace(updated)
        self.metrics.increment("v7_resource_transitions_total")
        self._record(resource_id, "lifecycle", lifecycle.value, actor)
        return updated

    def plan_recovery(
        self,
        resource_id: str,
        target_reference: str,
        *,
        rollback: bool = False,
        actor: str = "system",
    ) -> RecoveryPlan:
        resource = self.registry.get(resource_id)
        issues = []
        if "://" not in target_reference:
            issues.append("recovery target must be a reference")
        if resource.lifecycle is ResourceLifecycle.DELETED:
            issues.append("deleted resources cannot be recovered")
        plan = RecoveryPlan(
            str(uuid4()),
            resource_id,
            "rollback" if rollback else "recovery",
            target_reference,
            not issues,
            rollback,
            issues=tuple(issues),
        )
        self.recoveries.append(plan)
        self.metrics.increment("v7_resource_recoveries_total")
        self._record(
            resource_id,
            "recovery",
            "planned",
            actor,
            plan.recovery_id,
            {"ready": plan.ready, "rollback": rollback},
        )
        return plan

    def snapshot(self) -> dict[str, object]:
        resources = self.registry.list()
        history = tuple(self.history)
        return {
            "catalog": serialize(self.catalog.list()),
            "registry": serialize(resources),
            "capacity": serialize(tuple(self.capacity_history)),
            "reservations": serialize(tuple(self.reservations)),
            "dependencies": serialize(
                tuple(
                    {
                        "resource_id": item.resource_id,
                        "dependencies": item.dependency_references,
                    }
                    for item in resources
                )
            ),
            "constraints": serialize(
                tuple(
                    {"resource_id": item.resource_id, "constraints": item.constraints}
                    for item in resources
                )
            ),
            "planner": serialize(tuple(self.plans)),
            "recovery": serialize(tuple(self.recoveries)),
            "lifecycle": serialize(
                tuple(
                    {"resource_id": item.resource_id, "lifecycle": item.lifecycle}
                    for item in resources
                )
            ),
            "history": serialize(history),
            "metrics": self.metrics.snapshot(),
            "audit": serialize(history),
            "health": {
                "status": "healthy",
                "resources": len(resources),
                "available": sum(
                    item.availability.available
                    and item.lifecycle is not ResourceLifecycle.DELETED
                    for item in resources
                ),
                "ready_plans": sum(plan.ready for plan in self.plans),
                "advisory_only": True,
                "runtime_allocation_enabled": False,
            },
        }


GLOBAL_RESOURCE_FRAMEWORK = ResourceFramework()

__all__ = (
    "DependencyCycleError",
    "GLOBAL_RESOURCE_FRAMEWORK",
    "IllegalLifecycleTransition",
    "LIFECYCLE_TRANSITIONS",
    "METRIC_NAMES",
    "Metrics",
    "ReservationConflictError",
    "ResourceCatalog",
    "ResourceFramework",
    "ResourceFrameworkError",
    "ResourceRegistry",
    "ResourceSecurity",
    "ResourceValidationError",
    "TracingHooks",
)
