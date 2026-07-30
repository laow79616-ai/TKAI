"""Offline, mock-only validation for the TKAI V10 Sovereign Core."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tkai.v10 import (
    Attestation,
    Boundary,
    ChangePlan,
    Context,
    IntegrityRecord,
    Lifecycle,
    Principal,
    PrincipalType,
    Reference,
    Scope,
    SovereignCore,
    SovereignCoreModel,
    TopologyEdge,
    TrustDomain,
)
from tkai.v10.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.compatibility import COMPATIBILITY_KINDS, negotiate
from tkai.v10.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.events import EVENT_NAMES
from tkai.v10.metrics import METRICS
from tkai.v10.registries import BoundedRegistry, RegistryError
from tkai.v10.security import authorize_scope, filter_secrets, validate_safe_metadata
from tkai.v10.topology import EDGE_KINDS, MetadataTopology


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_path_package_structure_and_immutable_model() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        "sovereign_core trust attestations integrity identities principals policies "
        "constraints governance boundaries control_plane frameworks capabilities "
        "services modules extensions runtime contexts registries discovery topology "
        "dependencies relationships compatibility negotiation planning changes "
        "versions configuration storage events state security observability "
        "diagnostics health metrics audit contracts interfaces lifecycle "
        "dashboard api".split()
    )
    assert required <= {
        path.name for path in (root / "src/tkai/v10").iterdir() if path.is_dir()
    }
    model = SovereignCoreModel()
    assert model.core_version == "10.0.0"
    assert {"local-first", "advisory", "bounded", "reference-only"} <= model.tags
    with pytest.raises(FrozenInstanceError):
        model.owner = "changed"  # type: ignore[misc]
    assert len(Lifecycle) == 16


def test_trust_identity_principal_scope_and_rbac_metadata() -> None:
    scope = Scope("tenant", "workspace", "namespace")
    domain = TrustDomain("td", "domain", scope)
    principal = Principal(
        "p",
        PrincipalType.USER,
        "identity:user",
        role_references=("reader",),
        permission_references=("metadata:read",),
        scope=scope,
    )
    core = SovereignCore()
    core.register("trust_domains", domain)
    core.register("principals", principal)
    assert core.discover("principals") == (principal,)
    authorize_scope(scope, scope)
    for other, message in (
        (Scope("other", "workspace", "namespace"), "tenant isolation"),
        (Scope("tenant", "other", "namespace"), "workspace isolation"),
        (Scope("tenant", "workspace", "other"), "namespace isolation"),
    ):
        with pytest.raises(PermissionError, match=message):
            authorize_scope(scope, other)


def test_integrity_attestations_boundaries_are_reference_only() -> None:
    core = SovereignCore()
    integrity = IntegrityRecord("i", "subject", "package", expected_hash="abc")
    attestation = Attestation("a", "subject", "framework", "local:issuer")
    boundary = Boundary(
        "b",
        "workspace",
        allowed_references=("subject",),
        restricted_references=("other",),
    )
    core.register("integrity", integrity)
    core.register("attestations", attestation)
    core.register("boundaries", boundary)
    assert integrity.verification_status == "unverified"
    assert attestation.status == "registered"
    assert not hasattr(core, "attest_automatically")
    assert not hasattr(core, "grant_trust")


def test_bounded_registry_discovery_contexts_and_secret_filtering() -> None:
    registry = BoundedRegistry("test", limit=1)
    registry.register(Reference("one"))
    with pytest.raises(RegistryError, match="limit"):
        registry.register(Reference("two"))
    with pytest.raises(RegistryError, match="result limit"):
        registry.discover(limit=501)
    now = datetime.now(timezone.utc)
    core = SovereignCore()
    core.add_context(Context("c", time_range=(now, now + timedelta(hours=1))))
    with pytest.raises(ValueError, match="time range"):
        core.add_context(Context("long", time_range=(now, now + timedelta(days=367))))
    with pytest.raises(ValueError, match="secret-bearing"):
        validate_safe_metadata({"api_key": "x"})
    assert filter_secrets({"password": "x", "nested": {"cookie": "y"}}) == {
        "password": "[REDACTED]",
        "nested": {"cookie": "[REDACTED]"},
    }


def test_topology_dependency_detection_and_bounds() -> None:
    topology = MetadataTopology(max_nodes=2, max_edges=3)
    topology.add_node(
        Reference("a", integrity_reference="i", attestation_reference="t")
    )
    topology.add_node(Reference("b", "2.0.0"))
    topology.add_edge(TopologyEdge("a", "b", required_version="1.0.0"))
    topology.add_edge(TopologyEdge("b", "a"))
    topology.add_edge(TopologyEdge("a", "missing"))
    codes = {issue["code"] for issue in topology.issues()}
    assert {
        "missing-dependency",
        "circular-dependency",
        "version-conflict",
        "integrity-gap",
        "attestation-gap",
    } <= codes
    assert {"trust", "integrity", "attestation", "security"} <= EDGE_KINDS
    with pytest.raises(ValueError, match="node count"):
        topology.add_node(Reference("c"))


def test_policy_awareness_compatibility_and_change_planning_are_advisory() -> None:
    core = SovereignCore()
    result = core.evaluate_policy(paused=True, maintenance=True, kill_switch=True)
    assert result["eligible"] is False
    assert result["policy_execution"] is False
    for source in ("v6", "v7", "v8", "v9"):
        first = negotiate(source)
        assert first == negotiate(source)
        assert first["compatible"] is True
        assert first["automatic_migration"] is False
    assert len(COMPATIBILITY_KINDS) == 18
    plan = ChangePlan("cp", "subject", "current", "proposed", confidence=0.8)
    planned = core.plan(plan)
    assert plan.executable is False
    assert planned["application"] == "disabled"
    assert planned["runtime_mutation"] is False
    assert planned["automatic_approval"] is False


def test_validation_diagnostics_health_metrics_events_dashboard_and_audit() -> None:
    core = SovereignCore()
    assert core.validation()["valid"] is True
    assert core.health()["liveness"] is True
    assert set(core.metrics()) == set(METRICS)
    assert len(METRICS) == 21
    assert len(EVENT_NAMES) == 19
    assert core.audit()
    projection = dashboard_snapshot(core)
    assert len(DASHBOARD_SECTIONS) == 31
    assert projection["read_only"] is True and projection["actions"] == ()
    core.set_lifecycle_reference(Lifecycle.APPROVED_REFERENCE)
    assert core.lifecycle()["reference_states_execute"] is False


def test_api_openapi_and_server_integration_are_get_only() -> None:
    app = FakeApp()
    register_routes(app)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert len(GET_ROUTES) == 31
    contract = openapi_contract()
    assert all(set(operations) == {"get"} for operations in contract["paths"].values())
    forbidden = (
        "apply",
        "execute",
        "mutate",
        "restart",
        "restore",
        "migrate",
        "upgrade",
        "approve",
        "secret",
        "start",
        "stop",
        "allocate",
    )
    assert not any(word in route for route in GET_ROUTES for word in forbidden)
    root = Path(__file__).resolve().parents[3]
    source = (root / "server/api/app.py").read_text(encoding="utf-8")
    assert "register_v10_sovereign_core_routes(app)" in source


def test_local_only_surface_has_no_execution_or_network_capabilities() -> None:
    core = SovereignCore()
    overview = core.overview()
    assert overview["execution"] == "disabled"
    assert overview["runtime_mutation"] is False
    assert overview["remote_control_plane"] is False
    assert overview["external_network_calls"] is False
    forbidden_attributes = (
        "execute",
        "apply",
        "migrate",
        "upgrade",
        "rollback",
        "restart",
        "scan_filesystem",
        "network_client",
        "browser",
        "publish",
    )
    assert not any(hasattr(core, name) for name in forbidden_attributes)
