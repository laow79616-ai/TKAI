"""Mock-only tests for the V9 Adaptive Governance Mesh."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.governance_mesh.analytics import coverage_summary
from tkai.v9.governance_mesh.api import (
    GET_ROUTES,
    openapi_contract,
    register_routes,
)
from tkai.v9.governance_mesh.approvals import authorizes_execution
from tkai.v9.governance_mesh.boundaries import BOUNDARY_TYPES
from tkai.v9.governance_mesh.compliance import enforces_compliance
from tkai.v9.governance_mesh.contracts import (
    ApprovalRecord,
    BoundaryRecord,
    CompatibilityRecord,
    ComplianceRecord,
    ConstraintRecord,
    GovernanceProfile,
    GovernanceReference,
    GovernanceScope,
    PolicyRecord,
    ReviewRecord,
)
from tkai.v9.governance_mesh.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh
from tkai.v9.governance_mesh.governance import PolicyFabric
from tkai.v9.governance_mesh.relationships import GovernanceRelationship
from tkai.v9.governance_mesh.security import (
    GovernanceAccessController,
    GovernancePrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def get(self, path: str, **kwargs: object):  # type: ignore[no-untyped-def]
        def decorator(handler: object) -> object:
            self.routes[path] = ("GET", handler)
            return handler

        return decorator


def reference(identifier: str, generation: str = "v8") -> GovernanceReference:
    return GovernanceReference(identifier, "1.0", generation=generation)


def profile() -> GovernanceProfile:
    return GovernanceProfile(
        "profile-1",
        "9.0.0",
        "platform-governance",
        framework_references=(reference("framework"),),
        policy_references=(reference("policy"),),
        constraint_references=(reference("constraint"),),
        compliance_references=(reference("compliance"),),
        boundary_references=(reference("boundary"),),
        review_references=(reference("review"),),
        approval_references=(reference("approval"),),
        compatibility_references=(reference("compatibility"),),
        health="healthy",
        metrics={"coverage": 1.0},
        audit=({"event": "created"},),
        metadata={"mode": "reference-only"},
    )


def test_governance_profile_is_complete_immutable_and_advisory() -> None:
    value = profile()
    assert value.profile_id == "profile-1"
    assert value.execution_authorized is False
    assert value.approval_references[0].identifier == "approval"
    with pytest.raises(TypeError):
        value.metadata["mode"] = "runtime"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        value.owner = "other"  # type: ignore[misc]


def test_policy_fabric_aggregates_all_generations_by_reference_only() -> None:
    fabric = PolicyFabric()
    result = fabric.aggregate(
        v6_governance_centers=({"identifier": "v6-governance"},),
        v7_frameworks=({"identifier": "v7-framework"},),
        v8_frameworks=({"identifier": "v8-framework"},),
        v9_components=({"identifier": "v9-component"},),
    )
    assert {items[0].generation for items in result.values()} == {
        "v6",
        "v7",
        "v8",
        "v9",
    }
    assert fabric.enforces_policies() is False
    assert fabric.mutates_runtime_state() is False


def test_policies_constraints_boundaries_and_relationships_are_metadata() -> None:
    fabric = AdaptiveGovernanceMesh()
    policy = PolicyRecord(
        "policy-1",
        "Mock policy",
        framework_references=(reference("framework-1"),),
        rule_references=(reference("rule-1"),),
        constraint_references=(reference("constraint-1"),),
    )
    constraint = ConstraintRecord(
        "constraint-1",
        "Mock constraint",
        policy_references=(reference("policy-1"),),
        boundary_references=(reference("boundary-1"),),
    )
    boundaries = tuple(
        BoundaryRecord(
            f"{boundary_type}-boundary",
            boundary_type,
            GovernanceScope("tenant-a", "workspace-a"),
        )
        for boundary_type in BOUNDARY_TYPES
    )
    fabric.register_policy(policy)
    fabric.register_constraint(constraint)
    for boundary in boundaries:
        fabric.register_boundary(boundary)
    fabric.add_relationship(
        GovernanceRelationship("policy-1", "constraint-1", "constrained_by")
    )
    snapshot = fabric.snapshot()
    assert snapshot["policies"][0]["enforced"] is False
    assert len(snapshot["boundaries"]) == 7
    assert snapshot["relationships"][0]["kind"] == "constrained_by"


def test_compliance_coverage_has_no_enforcement_runtime() -> None:
    record = ComplianceRecord(
        "compliance-1",
        summary="Mock-only compliance summary",
        policy_coverage=1.0,
        constraint_coverage=0.8,
        compatibility_coverage=0.9,
        review_coverage=0.7,
        approval_coverage=0.6,
        audit_coverage=1.0,
    )
    assert coverage_summary(record)["constraint"] == 0.8
    assert record.summary == "Mock-only compliance summary"
    assert coverage_summary(record)["approval"] == 0.6
    assert enforces_compliance(record) is False
    with pytest.raises(ValueError, match="between 0 and 1"):
        ComplianceRecord("invalid", policy_coverage=1.1)


def test_reviews_and_approvals_preserve_evidence_without_authorization() -> None:
    fabric = AdaptiveGovernanceMesh()
    review = ReviewRecord(
        "review-1",
        reviewer_references=(reference("reviewer-1"),),
        findings=("Mock finding",),
        recommendations=("Review mock coverage",),
        status="reviewed",
        audit_references=(reference("audit-1"),),
    )
    approval = ApprovalRecord(
        "approval-1",
        reference("policy-1"),
        approver_references=(reference("approver-1"),),
        status="approved-metadata",
        review_references=(reference("review-1"),),
        audit_references=(reference("audit-2"),),
    )
    fabric.register_review(review)
    fabric.register_approval(approval)
    assert approval.execution_authorized is False
    assert authorizes_execution(approval) is False
    assert fabric.snapshot()["approvals"][0]["execution_authorized"] is False


def test_cross_version_compatibility_and_backward_imports() -> None:
    record = CompatibilityRecord(
        "compatibility-1",
        reference("v6-governance", "v6"),
        reference("v8-governance", "v8"),
    )
    fabric = AdaptiveGovernanceMesh()
    fabric.register_compatibility(record)
    assert fabric.snapshot()["compatibility"][0]["status"] == "compatible"

    from tkai.v7.runtime_governance import RuntimeGovernanceFramework
    from tkai.v8.hyper_coordination import HyperCoordinationFramework
    from tkai.v8.hyper_intelligence import HyperIntelligenceFabric

    assert RuntimeGovernanceFramework is not None
    assert HyperCoordinationFramework().overview()["execution"] == "disabled"
    assert HyperIntelligenceFabric().overview()["execution"] == "disabled"


def test_security_observability_diagnostics_health_and_metrics() -> None:
    fabric = AdaptiveGovernanceMesh(
        metadata={"api_key": "mock-secret", "visible": "safe"}
    )
    controller = GovernanceAccessController()
    principal = GovernancePrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
    )
    controller.authorize(
        principal,
        "governance:read",
        GovernanceScope("tenant-a", "workspace-a"),
    )
    with pytest.raises(PermissionError, match="tenant isolation"):
        controller.authorize(
            principal,
            "governance:read",
            GovernanceScope("tenant-b", "workspace-a"),
        )
    with pytest.raises(PermissionError, match="workspace isolation"):
        controller.authorize(
            principal,
            "governance:read",
            GovernanceScope("tenant-a", "workspace-b"),
        )
    fabric.register_policy(PolicyRecord("unlinked-policy", "Unlinked"))
    fabric.register_review(ReviewRecord("pending-review"))
    fabric.observability.log("info", "mock structured log", {"token": "secret"})
    fabric.observability.trace("governance-read", "mock-correlation")
    snapshot = fabric.snapshot()
    assert fabric.metadata["api_key"] == "[REDACTED]"
    assert snapshot["logs"][0]["metadata"]["token"] == "[REDACTED]"
    assert snapshot["traces"]
    assert snapshot["audit"]
    assert {item["code"] for item in snapshot["diagnostics"]} == {
        "policy-without-framework",
        "review-pending",
    }
    assert fabric.health()["status"] == "healthy"
    assert fabric.metrics()["policies"] == 1


def test_dashboard_api_and_openapi_are_read_only() -> None:
    fabric = AdaptiveGovernanceMesh()
    fabric.register_profile(profile())
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["sections"] == DASHBOARD_SECTIONS
    assert dashboard["read_only"] is True
    assert set(DASHBOARD_SECTIONS) == {
        "Governance Overview",
        "Federation",
        "Policies",
        "Constraints",
        "Compliance",
        "Reviews",
        "Approvals",
        "Compatibility",
        "Diagnostics",
        "Health",
        "Metrics",
        "Audit",
    }
    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert set(paths) == set(GET_ROUTES)
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.approves_execution() is False
    assert fabric.enforces_compliance() is False
