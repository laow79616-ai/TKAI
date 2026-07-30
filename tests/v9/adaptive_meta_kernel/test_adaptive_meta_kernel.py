"""Offline, mock-only validation for the TKAI V9 Adaptive Meta-Kernel."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tkai.v9.api import GET_ROUTES, register_routes
from tkai.v9.compatibility import negotiate_generations, negotiate_version
from tkai.v9.contracts import (
    AdaptationProfile,
    ChangePlan,
    Context,
    Lifecycle,
    MetaKernelModel,
    Reference,
    Scope,
    TopologyEdge,
)
from tkai.v9.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.events import EVENT_NAMES
from tkai.v9.meta_kernel import V7_FRAMEWORKS, V8_FRAMEWORKS, AdaptiveMetaKernel
from tkai.v9.metrics import METRICS
from tkai.v9.registry import BoundedRegistry, RegistryError
from tkai.v9.security import authorize_scope, filter_secrets
from tkai.v9.topology import MetadataTopology


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_path_and_required_package_structure() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = {
        "meta_kernel",
        "topology",
        "frameworks",
        "capabilities",
        "services",
        "modules",
        "extensions",
        "runtime",
        "contexts",
        "adaptation",
        "policies",
        "constraints",
        "compatibility",
        "negotiation",
        "planning",
        "changes",
        "versions",
        "registry",
        "discovery",
        "dependencies",
        "relationships",
        "state",
        "events",
        "configuration",
        "security",
        "governance",
        "observability",
        "diagnostics",
        "health",
        "metrics",
        "audit",
        "contracts",
        "interfaces",
        "lifecycle",
        "dashboard",
        "api",
    }
    assert required <= {
        path.name for path in (root / "src/tkai/v9").iterdir() if path.is_dir()
    }


def test_kernel_model_is_immutable_and_reference_only() -> None:
    model = MetaKernelModel()
    assert model.kernel_version == "9.0.0"
    assert {"advisory", "reference-only", "local"} <= model.tags
    with pytest.raises(FrozenInstanceError):
        model.owner = "changed"  # type: ignore[misc]
    assert set(Lifecycle) == {
        Lifecycle(value)
        for value in (
            "draft",
            "registered",
            "validating",
            "ready",
            "observing",
            "assessing",
            "planning_reference",
            "reviewed",
            "approved_reference",
            "paused",
            "maintenance",
            "superseded",
            "archived",
            "deleted",
        )
    }


def test_defaults_cover_v6_v7_v8_and_read_only_policy_sources() -> None:
    kernel = AdaptiveMetaKernel()
    identifiers = {
        item.identifier for item in kernel.framework_registry.discover(limit=100)
    }
    assert len(V8_FRAMEWORKS) == 11 and len(V7_FRAMEWORKS) == 15
    assert {f"v8-{name}" for name in V8_FRAMEWORKS} <= identifiers
    assert {f"v7-{name}" for name in V7_FRAMEWORKS} <= identifiers
    assert "v6-tiktok-ai-centers" in identifiers
    assert len(kernel.registries.policies) == 6
    assert kernel.overview()["execution"] == "disabled"


def test_bounded_registry_discovery_and_isolation() -> None:
    registry = BoundedRegistry("test", limit=2)
    tenant_a = Scope("a", "work", "ns")
    registry.register(Reference("one", scope=tenant_a))
    registry.register(Reference("two", scope=Scope("b", "work", "ns")))
    assert [item.identifier for item in registry.discover(scope=tenant_a)] == ["one"]
    with pytest.raises(RegistryError, match="limit"):
        registry.register(Reference("three"))
    with pytest.raises(RegistryError, match="result limit"):
        registry.discover(limit=501)
    with pytest.raises(ValueError, match="executable permissions"):
        Reference("executor", permissions=frozenset({"execute"}))


def test_dependency_graph_detects_missing_cycles_and_version_conflicts() -> None:
    topology = MetadataTopology(max_nodes=3, max_edges=4)
    topology.add_node(Reference("a", "1.0.0"))
    topology.add_node(Reference("b", "2.0.0"))
    topology.add_edge(TopologyEdge("a", "b", required_version="1.0.0"))
    topology.add_edge(TopologyEdge("b", "a"))
    topology.add_edge(TopologyEdge("a", "missing"))
    codes = {issue["code"] for issue in topology.issues()}
    assert {"missing-dependency", "circular-dependency", "version-conflict"} <= codes
    with pytest.raises(ValueError, match="edge kind"):
        topology.add_edge(TopologyEdge("a", "b", "execute"))


def test_context_isolation_secret_filtering_and_bounded_time() -> None:
    kernel = AdaptiveMetaKernel(register_defaults=False)
    scope = Scope("tenant", "workspace", "namespace")
    now = datetime.now(timezone.utc)
    context = Context(
        "context-1",
        scope,
        (now, now + timedelta(hours=1)),
        safe_metadata={"purpose": "test"},
    )
    assert kernel.add_context(context) is context
    authorize_scope(scope, scope)
    with pytest.raises(PermissionError, match="tenant isolation"):
        authorize_scope(scope, Scope("other", "workspace", "namespace"))
    with pytest.raises(ValueError, match="time range"):
        kernel.add_context(Context("long", time_range=(now, now + timedelta(days=367))))
    assert filter_secrets({"password": "x", "nested": {"api_key": "y"}}) == {
        "password": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]"},
    }


def test_adaptations_and_change_plans_can_never_execute_or_apply() -> None:
    kernel = AdaptiveMetaKernel(register_defaults=False)
    profile = AdaptationProfile("a1", "c1", "subject", "current", "proposed", "trigger")
    plan = ChangePlan("p1", "subject", "current", "proposed")
    assert profile.executable is False and plan.executable is False
    assert kernel.assess(profile)["execution"] == "disabled"
    blocked = kernel.assess(
        AdaptationProfile("a2", "c1", "subject", "current", "proposed", "trigger"),
        paused=True,
        maintenance=True,
        kill_switch=True,
    )
    assert blocked["eligible"] is False
    assert blocked["blocked_by"] == ("paused", "maintenance", "kill-switch")
    result = kernel.plan(plan)
    assert result["application"] == "disabled" and result["runtime_mutation"] is False


def test_compatibility_and_version_negotiation_are_deterministic() -> None:
    first = negotiate_version("9.1.0", ("8.0.0", "9.0.0", "9.2.0"))
    second = negotiate_version("9.1.0", ("9.2.0", "9.0.0", "8.0.0"))
    assert first == second
    assert first.selected_reference == "9.2.0"
    assert first.migration_applied is False
    for source, target in (("v6", "v7"), ("v7", "v8"), ("v8", "v9"), ("v6", "v9")):
        assert negotiate_generations(source, target)["compatible"] is True
        assert negotiate_generations(source, target)["automatic_migration"] is False


def test_health_metrics_events_audit_dashboard_and_lifecycle() -> None:
    kernel = AdaptiveMetaKernel()
    assert kernel.health()["status"] == "healthy"
    assert set(kernel.metrics()) == set(METRICS)
    assert len(EVENT_NAMES) == 15
    assert kernel.audit()
    snapshot = dashboard_snapshot(kernel)
    assert len(DASHBOARD_SECTIONS) == 20
    assert snapshot["read_only"] is True and snapshot["actions"] == ()
    kernel.set_lifecycle_reference(Lifecycle.APPROVED_REFERENCE)
    assert kernel.lifecycle()["approved_reference_executes"] is False


def test_api_and_server_integration_are_get_only_and_have_no_forbidden_routes() -> None:
    app = FakeApp()
    register_routes(app)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    required = {
        "/v9/kernel",
        "/v9/kernel/frameworks",
        "/v9/kernel/capabilities",
        "/v9/kernel/services",
        "/v9/kernel/modules",
        "/v9/kernel/extensions",
        "/v9/kernel/topology",
        "/v9/kernel/dependencies",
        "/v9/kernel/contexts",
        "/v9/kernel/adaptations",
        "/v9/kernel/policies",
        "/v9/kernel/constraints",
        "/v9/kernel/compatibility",
        "/v9/kernel/version-negotiation",
        "/v9/kernel/change-plans",
        "/v9/kernel/validation",
        "/v9/kernel/diagnostics",
        "/v9/kernel/health",
        "/v9/kernel/metrics",
        "/v9/kernel/audit",
        "/v9/kernel/lifecycle",
    }
    assert required == set(GET_ROUTES)
    forbidden = (
        "apply",
        "execute",
        "mutate",
        "restart",
        "restore",
        "migrate",
        "approve",
        "secret",
    )
    assert not any(word in route for route in GET_ROUTES for word in forbidden)
    root = Path(__file__).resolve().parents[3]
    server_source = (root / "server/api/app.py").read_text(encoding="utf-8")
    assert "register_v9_meta_kernel_routes(app)" in server_source
