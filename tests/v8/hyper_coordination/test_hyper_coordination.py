"""Offline tests for the V8 Hyper Coordination Framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_coordination.api import (
    GET_ROUTES,
    openapi_contract,
    register_routes,
)
from tkai.v8.hyper_coordination.contracts import (
    CoordinationEdge,
    CoordinationLifecycle,
    CoordinationProfile,
    CoordinationScope,
    GovernanceReferences,
    GraphKind,
    Reference,
)
from tkai.v8.hyper_coordination.coordination import HyperCoordinationFramework
from tkai.v8.hyper_coordination.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v8.hyper_coordination.lifecycle import authorizes_execution
from tkai.v8.hyper_coordination.registry import CoordinationRegistryError
from tkai.v8.hyper_coordination.security import (
    CoordinationAccessController,
    CoordinationPrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def get(self, path: str, **kwargs: object):  # type: ignore[no-untyped-def]
        def decorator(handler: object) -> object:
            self.routes[path] = ("GET", handler)
            return handler

        return decorator


def profile(
    profile_id: str = "coordination-profile",
    scope: CoordinationScope | None = None,
) -> CoordinationProfile:
    return CoordinationProfile(
        profile_id=profile_id,
        name="Coordination Profile",
        description="Offline metadata coordination",
        version="8.0.0",
        owner="platform",
        framework_references=(Reference("v8-hyper-kernel", "8.0.0"),),
        capability_references=(Reference("metadata-coordination"),),
        dependency_references=(Reference("v8-hyper-kernel"),),
        relationship_references=(Reference("v7-frameworks"),),
        compatibility=(Reference("v6-ai-centers", "6.x"),),
        metrics={"references": 5},
        audit=({"event": "created"},),
        metadata={"mode": "reference-only"},
        scope=scope or CoordinationScope(),
    )


def test_profiles_are_complete_immutable_and_reference_only() -> None:
    value = profile()

    assert value.profile_id == "coordination-profile"
    assert value.framework_references[0].identifier == "v8-hyper-kernel"
    assert value.execution_authorized is False
    with pytest.raises(TypeError):
        value.metadata["mode"] = "execute"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        value.owner = "other"  # type: ignore[misc]


def test_registry_defaults_isolation_and_duplicates() -> None:
    framework = HyperCoordinationFramework()
    assert {item.generation for item in framework.registries.frameworks.discover()} == {
        "v6",
        "v7",
        "v8",
        "future",
    }
    scoped = profile(scope=CoordinationScope("tenant-a", "workspace-a", "f-a"))
    framework.register_profile(scoped)
    assert framework.registries.profiles.discover(
        CoordinationScope("tenant-a", "workspace-a", "*")
    ) == (scoped,)
    assert not framework.registries.profiles.discover(
        CoordinationScope("tenant-b", "workspace-a", "*")
    )
    with pytest.raises(CoordinationRegistryError):
        framework.register_profile(scoped)


def test_all_reference_graphs_exist_and_no_execution_graph_exists() -> None:
    framework = HyperCoordinationFramework()
    for kind in GraphKind:
        framework.add_edge(CoordinationEdge("source", "target", kind))
    snapshot = framework.graph.snapshot()
    assert set(snapshot) == {kind.value for kind in GraphKind}
    assert "execution" not in snapshot


def test_dependency_cycle_is_diagnostic_not_execution() -> None:
    framework = HyperCoordinationFramework()
    framework.add_edge(CoordinationEdge("a", "b", GraphKind.FRAMEWORK))
    framework.add_edge(CoordinationEdge("b", "a", GraphKind.FRAMEWORK))
    assert framework.health()["status"] == "degraded"
    assert framework.diagnostics()[0]["code"] == "coordination-cycle"
    assert framework.overview()["execution"] == "disabled"


def test_metadata_synchronization_only() -> None:
    framework = HyperCoordinationFramework()
    source = Reference("source", "1")
    target = Reference("target", "2")
    record = framework.plan_synchronization(
        "version", source, target, {"recommended": "2"}
    )
    assert record.status == "pending"
    assert framework.synchronizer.runtime_synchronization_enabled() is False
    with pytest.raises(ValueError, match="unsupported synchronization"):
        framework.plan_synchronization("runtime", source, target)


def test_governance_references_never_authorize_execution() -> None:
    framework = HyperCoordinationFramework()
    framework.set_governance(
        GovernanceReferences(
            policies=(Reference("policy-1"),),
            approvals=(Reference("approval-1"),),
            risks=(Reference("risk-1"),),
            reviews=(Reference("review-1"),),
            audits=(Reference("audit-1"),),
        )
    )
    governance = framework.snapshot()["governance"]
    assert governance["execution_authorized"] is False  # type: ignore[index]
    assert all(not authorizes_execution(item) for item in CoordinationLifecycle)


def test_security_scope_rbac_secret_filtering_and_audit() -> None:
    framework = HyperCoordinationFramework(
        metadata={"api_key": "secret", "safe": "visible"}
    )
    access = CoordinationAccessController()
    principal = CoordinationPrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
        frameworks=frozenset({"framework-a"}),
    )
    access.authorize(
        principal,
        "coordination:read",
        CoordinationScope("tenant-a", "workspace-a", "framework-a"),
    )
    with pytest.raises(PermissionError, match="tenant isolation"):
        access.authorize(
            principal,
            "coordination:read",
            CoordinationScope("tenant-b", "workspace-a", "framework-a"),
        )
    with pytest.raises(PermissionError, match="framework isolation"):
        access.authorize(
            principal,
            "coordination:read",
            CoordinationScope("tenant-a", "workspace-a", "framework-b"),
        )
    assert framework.metadata["api_key"] == "[REDACTED]"
    assert framework.observability.audit_records()


def test_health_metrics_dashboard_and_get_only_api() -> None:
    framework = HyperCoordinationFramework()
    framework.register_profile(profile())
    dashboard = dashboard_snapshot(framework)
    assert dashboard["sections"] == DASHBOARD_SECTIONS
    assert set(DASHBOARD_SECTIONS) == {
        "Coordination Overview",
        "Framework Registry",
        "Dependencies",
        "Relationships",
        "Synchronization",
        "Compatibility",
        "Governance",
        "Health",
        "Metrics",
        "Audit",
    }
    assert framework.health()["status"] == "healthy"
    assert framework.metrics()["profiles"] == 1

    app = FakeApp()
    register_routes(app, framework)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    contract = openapi_contract()
    assert all(set(item) == {"get"} for item in contract["paths"].values())  # type: ignore[union-attr]


def test_existing_v8_imports_remain_available() -> None:
    from tkai.v8.kernel import HyperKernel

    assert HyperKernel().overview()["execution"] == "disabled"
