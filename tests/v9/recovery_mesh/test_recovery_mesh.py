from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.recovery_mesh import (
    AdaptiveRecoveryMesh,
    Incident,
    Profile,
    Recommendation,
    RecoveryPlan,
    RecoveryScope,
    Reference,
    Snapshot,
)
from tkai.v9.recovery_mesh.api import GET_ROUTES, openapi_contract, route_handlers
from tkai.v9.recovery_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.recovery_mesh.security import authorize


def ref(identifier: str = "ref-1", framework: str = "v9_components") -> Reference:
    return Reference(identifier, generation="v9", framework=framework)


def scope() -> RecoveryScope:
    return RecoveryScope("tenant-a", "workspace-a", "recovery-a", "profile-a")


def test_recovery_profile_is_immutable_and_non_executable() -> None:
    profile = Profile(
        "p",
        "Recovery",
        "Reference-only",
        "9.0.0",
        "owner",
        "recovery-a",
        ref("tenant"),
        ref("workspace"),
        scope=scope(),
        incident_references=(ref("incident"),),
        rollback_references=(ref("rollback"),),
        snapshot_references=(ref("snapshot"),),
        checkpoint_references=(ref("checkpoint"),),
    )
    assert not profile.execution_authorized
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_federation_is_bounded_allowlisted_local_and_read_only() -> None:
    mesh = AdaptiveRecoveryMesh(maximum_sources=1)
    assert mesh.federate((ref(),))[0].identifier == "ref-1"
    assert not mesh.federation.mutates_upstream()
    with pytest.raises(ValueError, match="bounded"):
        mesh.federate((ref("one"), ref("two")))
    with pytest.raises(ValueError, match="allowlisted"):
        AdaptiveRecoveryMesh().federate((ref(framework="unknown"),))
    with pytest.raises(ValueError, match="network"):
        AdaptiveRecoveryMesh().federate(
            (Reference("remote", framework="v8_frameworks", metadata={"remote": True}),)
        )


def test_incident_recovery_rollback_snapshot_checkpoint_and_resilience() -> None:
    mesh = AdaptiveRecoveryMesh()
    incident = Incident(
        "incident-1",
        "high",
        {"affected": 2},
        (ref("evidence"),),
        ("No root-cause claim",),
        scope(),
    )
    records = {
        "recovery": RecoveryPlan(
            "plan-1",
            "Advisory plan",
            ref("incident"),
            readiness="review",
            scope=scope(),
        ),
        "rollback": RecoveryPlan("rollback-1", "Rollback", ref(), scope=scope()),
        "snapshots": Snapshot(
            "snapshot-1",
            "Snapshot",
            ref(),
            integrity="verified-reference",
            retention="30 days",
            scope=scope(),
        ),
        "checkpoints": RecoveryPlan(
            "checkpoint-1",
            "Checkpoint",
            ref(),
            eligibility="eligible-reference",
            scope=scope(),
        ),
        "continuity": RecoveryPlan(
            "continuity-1",
            "Continuity",
            ref(),
            recovery_objectives={"rto": "4h"},
            scope=scope(),
        ),
        "resilience": RecoveryPlan(
            "resilience-1",
            "Resilience",
            ref(),
            readiness="prepared-reference",
            scope=scope(),
        ),
    }
    mesh.register("incidents", incident)
    for name, record in records.items():
        mesh.register(name, record)
    snapshot = mesh.snapshot()
    assert snapshot["recovery"][0]["executable"] is False
    assert not records["snapshots"].restores_snapshot
    assert not records["resilience"].activates_degraded_mode


def test_recommendations_are_advisory_and_non_executable() -> None:
    recommendation = Recommendation(
        "recommendation-1",
        "recovery_review",
        ref("incident"),
        limitations=("manual review required",),
        scope=scope(),
    )
    assert recommendation.advisory
    assert not recommendation.executable


def test_security_isolates_scope_and_filters_secrets() -> None:
    actual = scope()
    assert authorize("read", actual, actual)
    assert not authorize("execute", actual, actual)
    assert not authorize(
        "read",
        actual,
        RecoveryScope("other", "workspace-a", "recovery-a", "profile-a"),
    )
    with pytest.raises(ValueError, match="secret"):
        AdaptiveRecoveryMesh(metadata={"nested": {"session": "no"}})


def test_health_metrics_dashboard_and_get_only_api() -> None:
    mesh = AdaptiveRecoveryMesh()
    assert mesh.health()["status"] == "healthy"
    assert "v9_recovery_mesh_recovery_references_total" in mesh.metrics()
    assert dashboard_snapshot(mesh)["sections"] == DASHBOARD_SECTIONS
    required = {
        "/v9/recovery/profiles",
        "/v9/recovery/federation",
        "/v9/recovery/incidents",
        "/v9/recovery/recovery",
        "/v9/recovery/rollback",
        "/v9/recovery/snapshots",
        "/v9/recovery/checkpoints",
        "/v9/recovery/continuity",
        "/v9/recovery/resilience",
        "/v9/recovery/recommendations",
        "/v9/recovery/compatibility",
        "/v9/recovery/health",
        "/v9/recovery/metrics",
    }
    assert required <= set(GET_ROUTES)
    assert set(route_handlers(mesh)) == set(GET_ROUTES)
    assert all(set(value) == {"get"} for value in openapi_contract()["paths"].values())
    prohibited = ("execute", "restore", "restart", "activate", "mutate")
    assert not any(any(term in route for term in prohibited) for route in GET_ROUTES)
    checks = (
        mesh.executes_recovery,
        mesh.executes_rollback,
        mesh.restores_snapshots,
        mesh.restarts_services,
        mesh.activates_degraded_mode,
        mesh.mutates_runtime_state,
    )
    assert not any(check() for check in checks)


def test_server_integration_registers_get_only_routes() -> None:
    from server.api.app import create_app

    app = create_app()
    methods = {
        route.path: route.methods
        for route in app.routes
        if route.path.startswith("/v9/recovery/")
    }
    assert set(GET_ROUTES) <= set(methods)
    assert all(value == {"GET"} for value in methods.values())
