from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_recovery.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_recovery.contracts import (
    Approval,
    FailureClassification,
    FailureKind,
    RecoveryLifecycle,
    RecoveryPlan,
    RecoveryProfile,
    RecoveryReference,
    RecoveryScope,
    SnapshotMetadata,
)
from tkai.v8.hyper_recovery.dashboard import DASHBOARD_SECTIONS
from tkai.v8.hyper_recovery.fabric import BoundedRecoveryAdapter, HyperRecoveryFabric
from tkai.v8.hyper_recovery.security import (
    RecoveryPrincipal,
    authorize_read,
    secure_metadata,
)


def ref(identifier: str = "reference") -> RecoveryReference:
    return RecoveryReference(identifier, generation="v8")


def test_profile_is_immutable_and_lifecycle_is_complete() -> None:
    profile = RecoveryProfile("profile-1", "Primary", "1", "owner")
    with pytest.raises(FrozenInstanceError):
        profile.name = "changed"  # type: ignore[misc]
    assert profile.authorizes_execution is False
    assert {item.value for item in RecoveryLifecycle} == {
        "draft",
        "registered",
        "assessing",
        "planning",
        "validating",
        "ready-for-review",
        "under-review",
        "approved-reference",
        "degraded",
        "recovering-reference",
        "restored-reference",
        "rejected",
        "superseded",
        "archived",
        "deleted",
    }


def test_sources_are_allowlisted_bounded_read_only_and_redacted() -> None:
    fabric = HyperRecoveryFabric()
    result = fabric.read_source("v8-hyper-kernel", [{"api_key": "value"}])
    assert result[0]["api_key"] == "[REDACTED]"
    assert BoundedRecoveryAdapter("source").read_only
    with pytest.raises(PermissionError):
        fabric.read_source("external-network", [])
    with pytest.raises(ValueError):
        BoundedRecoveryAdapter("source", 1).read([{}, {}])


def test_root_cause_and_redundancy_claims_need_evidence() -> None:
    with pytest.raises(ValueError, match="supporting evidence"):
        FailureClassification(
            "failure-1", FailureKind.RUNTIME, ref(), root_cause_claimed=True
        )


def test_recovery_artifacts_never_execute() -> None:
    plan = RecoveryPlan("plan-1", ref("profile"))
    snapshot = SnapshotMetadata(
        "snapshot-1",
        ref("source"),
        ref("subject"),
        "1",
        "now",
        ref("payload"),
        "sha256:abc",
    )
    approval = Approval(
        "approval-1", ref("plan"), "1", "artifact", "reviewer", "approved"
    )
    fabric = HyperRecoveryFabric()
    assert plan.executable is False
    assert snapshot.restorable is False
    assert approval.authorizes_execution is False
    assert not fabric.executes_recovery()
    assert not fabric.mutates_runtime_state()
    assert not fabric.restores_snapshots()
    assert not fabric.restores_checkpoints()
    assert not fabric.executes_rollback()
    assert not fabric.activates_degraded_mode()
    assert not fabric.allocates_resources()
    assert not fabric.performs_tiktok_actions()


def test_dependency_detection_and_explainable_evaluation() -> None:
    fabric = HyperRecoveryFabric()
    issues = fabric.validate_dependencies({"a": ("b", "missing"), "b": ("a",)})
    assert {item["code"] for item in issues} == {
        "missing-dependency",
        "circular-dependency",
    }
    result = fabric.evaluate("evaluation-1", "readiness", {"evidence": 0.5, "plan": 1})
    assert result.score == 0.75
    assert result.factors and result.weight_metadata and result.explanation_summary


def test_scope_isolation_and_secret_filtering() -> None:
    authorize_read(
        RecoveryPrincipal("reader"),
        RecoveryScope(),
    )
    with pytest.raises(PermissionError):
        authorize_read(
            RecoveryPrincipal("reader", tenant="other"),
            RecoveryScope(),
        )
    assert secure_metadata({"password": "secret"})["password"] == "[REDACTED]"


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []
        self.state = type("State", (), {})()

    def get(self, path: str, **_: object):
        def decorate(function):
            self.routes.append((path, ("GET",)))
            return function

        return decorate


def test_api_is_get_only_and_openapi_is_complete() -> None:
    app = FakeApp()
    register_routes(app)
    assert {path for path, _ in app.routes} == set(GET_ROUTES)
    assert all(methods == ("GET",) for _, methods in app.routes)
    contract = openapi_contract()
    assert set(contract["paths"]) == set(GET_ROUTES)
    assert all(set(item) == {"get"} for item in contract["paths"].values())
    forbidden = (
        "execute",
        "restart",
        "restore",
        "activate",
        "allocate",
        "mutate",
        "secrets",
    )
    assert not any(word in route for route in GET_ROUTES for word in forbidden)
    assert len(DASHBOARD_SECTIONS) == 32


def test_metrics_and_health_publish_safety_invariants() -> None:
    fabric = HyperRecoveryFabric(metadata={"session": "hidden"})
    assert fabric.metadata["session"] == "[REDACTED]"
    metrics = fabric.metrics()
    assert "v8_recovery_profiles_total" in metrics
    assert "v8_recovery_health_status" in metrics
    assert all(
        value == "disabled"
        for key, value in fabric.health().items()
        if key
        in {
            "execution",
            "runtime_mutation",
            "service_restart",
            "workflow_start",
            "scheduler_mutation",
            "resource_allocation",
            "snapshot_restoration",
            "checkpoint_restoration",
            "rollback_execution",
            "degraded_mode_activation",
            "automatic_approval",
            "external_network",
        }
    )
