from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

import pytest

from tkai.v7.resource_framework import (
    Availability,
    Capacity,
    DependencyCycleError,
    DependencyReference,
    IllegalLifecycleTransition,
    ReservationConflictError,
    Resource,
    ResourceConstraint,
    ResourceFramework,
    ResourceLifecycle,
    ResourceScope,
    ResourceSecurity,
    ResourceTypeContract,
)
from tkai.v7.resource_framework.api import (
    RESOURCE_ENDPOINTS,
    register_resource_framework_routes,
)
from tkai.v7.resource_framework.dashboard import ResourceDashboard
from tkai.v7.security import AccessController, Principal


def resource(
    resource_id: str = "resource-1",
    *,
    resource_type: str = "worker",
    dependencies: tuple[DependencyReference, ...] = (),
    constraints: tuple[ResourceConstraint, ...] = (),
    capacity: Capacity | None = None,
    availability: Availability | None = None,
    scope: ResourceScope | None = None,
) -> Resource:
    return Resource(
        resource_id=resource_id,
        resource_type=resource_type,
        category="compute",
        owner="kernel",
        version="1.0.0",
        scope=scope or ResourceScope("tenant-1", "workspace-1"),
        state={"token": "secret", "mode": "metadata"},
        capacity=capacity or Capacity(10, 2, 1),
        availability=availability or Availability(True, 7),
        dependency_references=dependencies,
        constraints=constraints,
        capabilities=frozenset({"planning", "metadata"}),
        tags=frozenset({"v7", "advisory"}),
        metadata={"api_key": "secret", "safe": "visible"},
    )


def test_required_packages_are_importable() -> None:
    packages = (
        "models registry catalog discovery planner capacity allocation reservations "
        "dependencies constraints validation snapshots history recovery contracts "
        "interfaces events state health metrics audit security lifecycle dashboard api"
    ).split()
    for package in packages:
        assert importlib.import_module(f"tkai.v7.resource_framework.{package}")


def test_registry_catalog_extensibility_and_secret_filtering() -> None:
    framework = ResourceFramework()
    framework.catalog.register_type(ResourceTypeContract("future_accelerator"))
    item = framework.register(resource(resource_type="future accelerator"))
    assert framework.registry.get(item.resource_id) == item
    assert item.state["token"] == "[REDACTED]"
    assert item.metadata["api_key"] == "[REDACTED]"
    with pytest.raises(FrozenInstanceError):
        item.owner = "other"  # type: ignore[misc]
    with pytest.raises(Exception, match="already registered"):
        framework.register(item)


def test_discovery_lookup_filter_tag_capability_dependency_and_metadata() -> None:
    framework = ResourceFramework()
    framework.register(resource("base"))
    framework.register(resource("child", dependencies=(DependencyReference("base"),)))
    discovered = framework.discover(resource_type="worker")
    assert [item.resource_id for item in discovered] == [
        "base",
        "child",
    ]
    assert framework.discover(capability="planning", tags=frozenset({"v7"}))
    assert framework.discover(dependency_id="base") == (
        framework.registry.get("child"),
    )
    assert framework.discover(metadata={"safe": "visible"})


def test_validation_dependencies_versions_constraints_capacity_and_cycles() -> None:
    framework = ResourceFramework()
    framework.register(
        replace(resource("a"), version="latest", capacity=Capacity(1, 2, 0))
    )
    framework.register(
        resource(
            "b",
            dependencies=(DependencyReference("a", "2.0.0"),),
            constraints=(ResourceConstraint("approved", False),),
        )
    )
    codes = {issue.code for issue in framework.validate("b").issues}
    assert codes == {"constraint_unsatisfied", "dependency_version_mismatch"}
    assert {issue.code for issue in framework.validate("a").issues} == {
        "capacity_invalid",
        "version_invalid",
    }

    cyclic = ResourceFramework()
    cyclic.register(resource("x", dependencies=(DependencyReference("y"),)))
    cyclic.register(resource("y", dependencies=(DependencyReference("x"),)))
    with pytest.raises(DependencyCycleError):
        cyclic._ordered_dependencies("x")
    assert "dependency_cycle" in {issue.code for issue in cyclic.validate("x").issues}


def test_capacity_reservation_expiry_history_and_conflicts_are_reference_only() -> None:
    framework = ResourceFramework()
    framework.register(resource())
    reservation = framework.reserve(
        "resource-1",
        2,
        "planner",
        reference="request://123",
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    )
    assert reservation.reference_only
    analysis = framework.analyze_capacity(
        "resource-1", growth_rate=0.2, historical_trend_references=("trend://1",)
    )
    assert analysis.available == 5
    assert analysis.growth_estimate == 2
    assert analysis.historical_trend_references == ("trend://1",)
    with pytest.raises(ReservationConflictError) as caught:
        framework.reserve("resource-1", 6, "planner")
    assert caught.value.conflict.conflicting_reservation_ids == (
        reservation.reservation_id,
    )
    expired = framework.expire_reservation(reservation.reservation_id)
    assert expired.status == "expired"
    assert len(framework.reservation_history) == 2


def test_planning_is_bounded_advisory_deterministic_and_never_allocates() -> None:
    framework = ResourceFramework(max_plan_size=3)
    framework.register(resource("a"))
    framework.register(resource("b", dependencies=(DependencyReference("a"),)))
    framework.register(resource("c", dependencies=(DependencyReference("b"),)))
    plan = framework.plan("c", requested_capacity=2)
    assert plan.ordered_resource_ids == ("a", "b", "c")
    assert plan.ready and plan.bounded and plan.advisory_only
    assert plan.runtime_allocation_enabled is False
    for unsafe in ("allocate", "execute", "start", "launch"):
        assert not hasattr(framework, unsafe)


def test_lifecycle_security_tenant_workspace_and_resource_isolation() -> None:
    access = AccessController({"operator": {"resource.transition"}})
    security = ResourceSecurity(access)
    framework = ResourceFramework(security=security)
    framework.register(resource())
    operator = Principal("operator", frozenset({"operator"}))
    updated = framework.transition(
        "resource-1",
        ResourceLifecycle.VALIDATED,
        principal=operator,
        tenant_reference="tenant-1",
        workspace_reference="workspace-1",
    )
    assert updated.lifecycle is ResourceLifecycle.VALIDATED
    with pytest.raises(IllegalLifecycleTransition):
        framework.transition(
            "resource-1",
            ResourceLifecycle.RESERVED,
            principal=operator,
        )
    with pytest.raises(PermissionError, match="tenant"):
        security.authorize(
            updated, "resource.transition", principal=operator, tenant_reference="other"
        )
    with pytest.raises(PermissionError, match="resource"):
        security.authorize(
            updated, "resource.transition", principal=operator, owner="other"
        )


def test_recovery_metrics_tracing_logging_health_and_audit() -> None:
    framework = ResourceFramework()
    traces: list[str] = []
    framework.tracing.register(lambda name, _attributes: traces.append(name))
    framework.register(resource(), actor="tester")
    framework.plan("resource-1", actor="tester")
    recovery = framework.plan_recovery(
        "resource-1", "snapshot://resource-1/v1", actor="tester"
    )
    rollback = framework.plan_recovery(
        "resource-1", "snapshot://resource-1/v0", rollback=True
    )
    projection = framework.snapshot()
    assert recovery.ready and recovery.reference_only and recovery.coordinated
    assert rollback.rollback
    assert projection["audit"] == projection["history"]
    assert projection["health"]["runtime_allocation_enabled"] is False  # type: ignore[index]
    assert projection["metrics"]["v7_resource_plans_total"] == 1  # type: ignore[index]
    assert traces == ["resource.registered", "resource.planned"]
    assert framework.logs


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, _endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, tuple(methods)))


def test_api_is_get_only_and_dashboard_has_required_sections() -> None:
    framework = ResourceFramework()
    app = FakeApp()
    register_resource_framework_routes(app, framework)
    assert {path for path, _ in app.routes} == {
        f"/v7/resources/{endpoint}" for endpoint in RESOURCE_ENDPOINTS
    }
    assert all(methods == ("GET",) for _, methods in app.routes)
    dashboard = ResourceDashboard(framework)
    assert set(dashboard.snapshot()) == set(dashboard.sections)


def test_v6_and_all_previous_v7_framework_imports_are_unchanged() -> None:
    assert importlib.import_module("tiktok.resource_center")
    assert importlib.import_module("tkai.v7.workflow_framework")
    assert importlib.import_module("tkai.v7.state_framework")
    assert importlib.import_module("tkai.v7.event_fabric")
    assert importlib.import_module("tkai.v7.service_mesh")
    assert importlib.import_module("tkai.v7.capabilities")
