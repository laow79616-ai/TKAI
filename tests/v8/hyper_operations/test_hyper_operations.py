"""Mock-only tests for the V8 Hyper Autonomous Operations Fabric."""

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_operations.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_operations.contracts import (
    CapacityMetadata,
    CompatibilityMetadata,
    DependencyKind,
    DependencyMetadata,
    HealthMetadata,
    MetricMetadata,
    OperationProfile,
    OperationsReference,
    OperationsScope,
    ReadinessKind,
    ReadinessMetadata,
    RecoveryMetadata,
    SummaryMetadata,
)
from tkai.v8.hyper_operations.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v8.hyper_operations.fabric import HyperOperationsFabric
from tkai.v8.hyper_operations.security import (
    OperationsAccessController,
    OperationsPrincipal,
    secure_metadata,
)


def ref(identifier: str, generation: str = "v8") -> OperationsReference:
    return OperationsReference(identifier, "1.0.0", generation)


def test_profile_is_complete_immutable_and_advisory() -> None:
    profile = OperationProfile(
        "profile-1",
        "8.0.0",
        "platform-operations",
        operation_references=(ref("operation"),),
        workflow_references=(ref("workflow"),),
        resource_references=(ref("resource"),),
        runtime_references=(ref("runtime"),),
        readiness_references=(ref("readiness"),),
        governance_references=(ref("governance"),),
        compatibility_references=(ref("compatibility"),),
        health="healthy",
        metrics={"availability": 1.0},
        audit=({"event": "created"},),
        metadata={"mode": "reference-only"},
    )
    assert profile.execution_eligible is False
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_readiness_covers_all_required_kinds_without_execution() -> None:
    fabric = HyperOperationsFabric()
    for kind in ReadinessKind:
        item = ReadinessMetadata(
            f"ready-{kind.value}", kind, ref(kind.value), True, "ready"
        )
        fabric.register_readiness(item)
        assert item.authorizes_execution is False
    assert {item["kind"] for item in fabric.snapshot()["readiness"]} == {
        item.value for item in ReadinessKind
    }


def test_summaries_dependencies_capacity_and_recovery_are_reference_only() -> None:
    fabric = HyperOperationsFabric()
    for name in (
        "operation",
        "workflow",
        "runtime",
        "dependency",
        "resource",
        "recovery",
    ):
        fabric.register_summary(
            SummaryMetadata(
                f"{name}-summary", name, ref(name), version_history=("1.0",)
            )
        )
    for kind in DependencyKind:
        fabric.register_dependency(
            DependencyMetadata(
                f"dep-{kind.value}", kind, ref("source"), ref("target"), available=True
            )
        )
    capacity = CapacityMetadata(
        "capacity-1", ref("resource"), 100, 80, 20, 10, (ref("forecast"),)
    )
    recovery = RecoveryMetadata(
        "recovery-1",
        ref("runtime"),
        rollback_references=(ref("rollback"),),
        readiness_references=(ref("ready"),),
        compatibility_references=(ref("compatible"),),
        governance_references=(ref("policy"),),
    )
    fabric.register_capacity(capacity)
    fabric.register_recovery(recovery)
    assert capacity.allocated is False
    assert recovery.performs_rollback is False


def test_v6_v7_v8_compatibility_and_bounded_aggregation() -> None:
    fabric = HyperOperationsFabric()
    for generation in ("v6", "v7", "v8"):
        fabric.register_compatibility(
            CompatibilityMetadata(
                f"compat-{generation}",
                ref("operations", generation),
                ref("fabric", "v8"),
            )
        )
    copied = fabric.aggregate_metadata(
        "v6-ai-centers", ({"name": "center", "api_token": "hidden"},)
    )
    assert copied[0]["api_token"] == "[REDACTED]"
    with pytest.raises(PermissionError):
        fabric.aggregate_metadata("unknown", ())


def test_recursive_secret_filtering_and_scope_isolation() -> None:
    secured = secure_metadata({"password": "x", "nested": {"access_token": "y"}})
    assert secured["password"] == "[REDACTED]"
    assert secured["nested"]["access_token"] == "[REDACTED]"  # type: ignore[index]
    controller = OperationsAccessController()
    principal = OperationsPrincipal("reader")
    controller.authorize(principal, "operations:read", OperationsScope())
    with pytest.raises(PermissionError, match="tenant"):
        controller.authorize(
            principal, "operations:read", OperationsScope(tenant="other")
        )
    with pytest.raises(PermissionError, match="workspace"):
        controller.authorize(
            principal, "operations:read", OperationsScope(workspace="other")
        )
    with pytest.raises(PermissionError, match="operations"):
        controller.authorize(
            principal, "operations:read", OperationsScope(operations="other")
        )
    with pytest.raises(PermissionError):
        controller.authorize(principal, "operations:write", OperationsScope())


def test_health_metrics_tracing_diagnostics_and_audit() -> None:
    fabric = HyperOperationsFabric()
    fabric.register_dependency(
        DependencyMetadata(
            "dep-1",
            DependencyKind.RUNTIME,
            ref("workflow"),
            ref("runtime"),
            available=False,
        )
    )
    fabric.register_health_record(
        HealthMetadata("health-1", ref("runtime"), "degraded")
    )
    fabric.register_metric(
        MetricMetadata("metric-1", "availability", 0.5, trace_reference=ref("trace"))
    )
    assert fabric.health()["status"] == "degraded"
    assert fabric.metrics()["v8_operations_execution_total"] == 0
    assert fabric.diagnostics()[0]["code"] == "required-dependency-unavailable"
    assert fabric.snapshot()["audit"]


def test_dashboard_has_all_required_read_only_sections() -> None:
    snapshot = dashboard_snapshot(HyperOperationsFabric())
    assert snapshot["read_only"] is True
    assert DASHBOARD_SECTIONS == (
        "Operations Overview",
        "Readiness",
        "Runtime",
        "Resources",
        "Dependencies",
        "Recovery",
        "Compatibility",
        "Health",
        "Metrics",
        "Audit",
    )


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def get(self, path: str, **kwargs: object):  # type: ignore[no-untyped-def]
        def decorator(handler: object) -> object:
            self.routes[path] = ("GET", handler)
            return handler

        return decorator


def test_api_is_get_only_and_has_no_execution_or_mutation_routes() -> None:
    app = FakeApp()
    register_routes(app)
    assert set(app.routes) == set(GET_ROUTES)
    assert all(method == "GET" for method, _ in app.routes.values())
    assert set(GET_ROUTES) == {
        "/v8/operations/profiles",
        "/v8/operations/readiness",
        "/v8/operations/runtime",
        "/v8/operations/resources",
        "/v8/operations/dependencies",
        "/v8/operations/recovery",
        "/v8/operations/compatibility",
        "/v8/operations/health",
        "/v8/operations/metrics",
    }
    forbidden = (
        "execute",
        "start",
        "mutate",
        "schedule",
        "browser",
        "account",
        "proxy",
        "device",
    )
    assert not any(word in route for route in GET_ROUTES for word in forbidden)
    contract = openapi_contract()
    assert all(set(methods) == {"get"} for methods in contract["paths"].values())


def test_fabric_has_no_operational_side_effects() -> None:
    fabric = HyperOperationsFabric()
    assert not fabric.executes_tiktok_actions()
    assert not fabric.mutates_runtime_state()
    assert not fabric.starts_workflows()
    assert not fabric.starts_schedules()
    assert not fabric.launches_browsers()
    assert not fabric.starts_accounts()
    assert not fabric.starts_proxies()
    assert not fabric.starts_devices()
    assert not fabric.allocates_resources()
