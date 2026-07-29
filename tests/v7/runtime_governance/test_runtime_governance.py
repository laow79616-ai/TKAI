from dataclasses import FrozenInstanceError

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.runtime_governance import (
    ActivationRecord,
    ApprovalReference,
    BoundaryKind,
    EligibilityKind,
    EligibilityRequest,
    GovernanceConstraint,
    GovernancePolicy,
    GovernanceProfile,
    IsolationError,
    KillSwitchMetadata,
    Lifecycle,
    PauseKind,
    PauseMetadata,
    RuntimeBoundary,
    RuntimeGovernanceFramework,
    RuntimeReference,
    Scope,
)
from tkai.v7.runtime_governance.api import (
    RUNTIME_GOVERNANCE_ENDPOINTS,
    register_runtime_governance_routes,
)
from tkai.v7.runtime_governance.dashboard import (
    SECTIONS,
    RuntimeGovernanceDashboard,
)


def build_framework() -> tuple[RuntimeGovernanceFramework, Scope]:
    framework = RuntimeGovernanceFramework()
    scope = Scope("tenant-a", "workspace-a")
    framework.register_policy(
        GovernancePolicy(
            "policy-1",
            "Advisory runtime policy",
            scope,
            runtime_metadata={"mode": "reference-only"},
            eligibility_metadata={"review": "required"},
            maintenance_metadata={"source": "declared"},
            pause_metadata={"source": "declared"},
            killswitch_metadata={"source": "declared"},
            compatibility_metadata={"v6": True},
            lifecycle=Lifecycle.APPROVED_REFERENCE,
        )
    )
    framework.register_constraint(
        GovernanceConstraint(
            "constraint-1",
            "configuration",
            "capability-1",
            ("config-present",),
            scope,
        )
    )
    boundary_references = []
    for kind in BoundaryKind:
        boundary = RuntimeBoundary(
            f"boundary-{kind.value}",
            kind,
            "capability-1",
            scope,
            (f"{kind.value}-isolated",),
        )
        framework.register_boundary(boundary)
        boundary_references.append(boundary.boundary_id)
    framework.register_runtime(
        RuntimeReference(
            "runtime-1",
            "Reference runtime",
            scope,
            capability_references=("capability-1",),
            boundary_references=tuple(boundary_references),
            readiness=True,
        )
    )
    framework.register_profile(
        GovernanceProfile(
            "profile-1",
            "Unified Governance",
            scope,
            "platform-owner",
            lifecycle=Lifecycle.READY,
            policy_references=("policy-1",),
            constraint_references=("constraint-1",),
            runtime_references=("runtime-1",),
            health="healthy",
            metrics={"readiness": 1},
            audit_reference="audit-1",
            metadata={"purpose": "advisory"},
        )
    )
    return framework, scope


def test_profile_contract_lifecycle_and_immutability() -> None:
    framework, scope = build_framework()
    profile = framework.registries["profiles"].get(
        "profile-1", GovernanceProfile, scope
    )
    assert profile.namespace == "runtime-governance"
    assert profile.tenant == "tenant-a"
    assert profile.workspace == "workspace-a"
    assert profile.version.compatibility_references == ("v6",)
    assert {item.value for item in Lifecycle} == {
        "draft",
        "registered",
        "validating",
        "ready",
        "review",
        "approved-reference",
        "paused",
        "maintenance",
        "archived",
        "deleted",
    }
    with pytest.raises(FrozenInstanceError):
        profile.lifecycle = Lifecycle.APPROVED_REFERENCE  # type: ignore[misc]


def test_policy_and_approval_never_authorize_execution() -> None:
    _, scope = build_framework()
    with pytest.raises(ValueError, match="never authorize"):
        GovernancePolicy(
            "unsafe-policy",
            "unsafe",
            scope,
            execution_authorized=True,
        )
    with pytest.raises(ValueError, match="never authorize"):
        ApprovalReference(
            "approval-1",
            "runtime-1",
            "reviewer",
            "approved-reference",
            scope,
            execution_authorized=True,
        )


@pytest.mark.parametrize("kind", list(EligibilityKind))
def test_read_only_eligibility_for_every_supported_kind(
    kind: EligibilityKind,
) -> None:
    framework, scope = build_framework()
    result = framework.evaluate_eligibility(
        EligibilityRequest(
            f"assessment-{kind.value}",
            kind,
            "capability-1",
            scope,
            ("policy-1",),
            ("constraint-1",),
            "runtime-1",
        )
    )
    assert result.eligible
    assert result.read_only
    assert not result.execution_authorized
    assert not hasattr(framework, "execute")
    assert not hasattr(framework, "approve_execution")


def test_pause_and_killswitch_are_metadata_only_and_affect_assessment() -> None:
    framework, scope = build_framework()
    framework.record_pause(
        PauseMetadata(
            "pause-1",
            PauseKind.EMERGENCY,
            "capability-1",
            "operator declaration",
            scope,
            active=True,
        )
    )
    framework.record_killswitch(
        KillSwitchMetadata(
            "killswitch-1",
            "Emergency declaration",
            "capability-1",
            "risk review",
            scope,
            active=True,
            activation_history=(
                ActivationRecord(
                    "activation-1",
                    True,
                    "risk review",
                    "capability-1",
                    "review-1",
                    "audit-2",
                ),
            ),
        )
    )
    result = framework.evaluate_eligibility(
        EligibilityRequest(
            "assessment-paused",
            EligibilityKind.CAPABILITY,
            "capability-1",
            scope,
            ("policy-1",),
            ("constraint-1",),
            "runtime-1",
        )
    )
    assert not result.eligible
    assert "active-pause-metadata" in result.reasons
    assert "active-killswitch-metadata" in result.reasons
    assert not hasattr(framework, "pause_runtime")
    assert not hasattr(framework, "activate_killswitch")


def test_boundary_scope_isolation_and_secret_filtering() -> None:
    framework, scope = build_framework()
    foreign = Scope("tenant-b", "workspace-a")
    with pytest.raises(IsolationError):
        framework.registries["runtime"].get("runtime-1", RuntimeReference, foreign)
    with pytest.raises(ValueError, match="unsafe metadata"):
        GovernanceProfile(
            "unsafe-profile",
            "unsafe",
            scope,
            "owner",
            metadata={"api_token": "must-not-be-stored"},
        )


def test_diagnostics_health_metrics_audit_and_dashboard() -> None:
    framework, scope = build_framework()
    assert framework.diagnose(scope) == ()
    health = framework.health(scope)
    assert health["framework_readiness"] is True
    assert health["runtime_execution"] is False
    assert health["runtime_mutation"] is False
    assert health["automatic_approval"] is False
    dashboard = RuntimeGovernanceDashboard(framework).snapshot(scope)
    assert set(dashboard) == set(SECTIONS)
    assert dashboard["overview"]["compatibility"]["v6_behavior_preserved"]
    assert dashboard["metrics"]["v7_runtime_governance_profiles_total"] == 1
    assert dashboard["audit"]
    assert framework.trace_hooks


def test_get_only_api_and_openapi_contract() -> None:
    framework, _ = build_framework()
    app = FastAPI()
    register_runtime_governance_routes(app, framework)
    client = TestClient(app)
    params = {"tenant": "tenant-a", "workspace": "workspace-a"}
    for endpoint in RUNTIME_GOVERNANCE_ENDPOINTS:
        path = f"/v7/runtime-governance/{endpoint}"
        assert client.get(path, params=params).status_code == 200
        assert client.post(path, params=params).status_code == 405
    paths = app.openapi()["paths"]
    assert all(
        set(paths[f"/v7/runtime-governance/{endpoint}"]) == {"get"}
        for endpoint in RUNTIME_GOVERNANCE_ENDPOINTS
    )
    assert not any(
        word in path
        for path in paths
        for word in ("execute", "approve-execution", "mutate-runtime")
    )


def test_v6_and_tiktok_imports_remain_compatible() -> None:
    import tiktok
    import tkai

    framework = RuntimeGovernanceFramework()
    assert framework.compatibility()["v6_behavior_preserved"] is True
    assert framework.compatibility()["tiktok_business_behavior_changed"] is False
    assert tkai is not None
    assert tiktok is not None
