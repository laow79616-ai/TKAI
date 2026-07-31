"""Offline tests for the V10 Sovereign Governance Mesh."""

from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.governance_mesh import (
    ApprovalReference,
    ApprovalStatus,
    CompatibilityGovernance,
    ComplianceDomain,
    ComplianceReference,
    ConstraintReference,
    ConstraintType,
    GovernanceDomain,
    GovernanceDomainRecord,
    GovernanceProfile,
    GovernanceRelationship,
    GovernanceValidation,
    PolicyReference,
    PolicyStatus,
    RelationshipType,
    ReviewReference,
    ReviewStatus,
    RiskLevel,
    RiskReference,
    SovereignGovernanceMesh,
    SubjectType,
    ValidationStatus,
    ValidationType,
)
from tkai.v10.governance_mesh.api import (
    GET_ROUTES,
    openapi_contract,
    register_routes,
)
from tkai.v10.governance_mesh.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v10.governance_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_structure_profile_and_domains() -> None:
    root = Path(__file__).resolve().parents[3]
    required = set(
        "profiles registry domains policies constraints reviews approvals risks "
        "compliance governance relationships compatibility planning validation "
        "diagnostics health metrics audit security events contracts interfaces "
        "lifecycle dashboard api".split()
    )
    package = root / "src/tkai/v10/governance_mesh"
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}
    profile = GovernanceProfile(
        "p", "subject", SubjectType.FRAMEWORK, GovernanceDomain.FRAMEWORK
    )
    assert profile.health == "unknown"
    assert len(SubjectType) == 14
    assert len(GovernanceDomain) == 14
    for domain in GovernanceDomain:
        item = GovernanceDomainRecord(domain.value, domain, "subject")
        assert item.reference_only is True


def test_policies_constraints_reviews_and_approvals_are_metadata_only() -> None:
    mesh = SovereignGovernanceMesh()
    for status in PolicyStatus:
        item = PolicyReference(status.value, "s", status, f"policy:{status.value}")
        mesh.register("policies", item)
        assert item.executable is False
    for kind in ConstraintType:
        item = ConstraintReference(kind.value, "s", kind, f"constraint:{kind.value}")
        mesh.register("constraints", item)
        assert item.reference_only is True
    for status in ReviewStatus:
        item = ReviewReference(f"review-{status.value}", "s", status)
        mesh.register("reviews", item)
        assert item.workflow_execution is False
    for status in ApprovalStatus:
        item = ApprovalReference(f"approval-{status.value}", "s", status)
        mesh.register("approvals", item)
        assert item.automatic_approval is False


def test_risks_compliance_relationships_and_validation() -> None:
    mesh = SovereignGovernanceMesh()
    for level in RiskLevel:
        mesh.register(
            "risks",
            RiskReference(
                level.value,
                "s",
                level,
                evidence_references=("evidence:local",),
                mitigation_references=("mitigation:local",),
            ),
        )
    for domain in ComplianceDomain:
        mesh.register(
            "compliance",
            ComplianceReference(
                domain.value, "s", domain, f"compliance:{domain.value}"
            ),
        )
    for kind in RelationshipType:
        item = GovernanceRelationship(kind.value, "s", "t", kind)
        mesh.register("relationships", item)
        assert item.reference_only is True
    for kind in ValidationType:
        item = GovernanceValidation(kind.value, "s", kind, ValidationStatus.PENDING)
        mesh.register("validation", item)
        assert item.metadata_only is True


def test_compatibility_health_metrics_observability_and_security() -> None:
    mesh = SovereignGovernanceMesh()
    compatibility = mesh.discover("compatibility")
    assert len(compatibility) == 5
    assert all(
        isinstance(item, CompatibilityGovernance)
        and not item.migration
        and not item.upgrade
        and not item.rollback
        for item in compatibility
    )
    mesh.register(
        "profiles",
        GovernanceProfile(
            "p",
            "s",
            SubjectType.MODULE,
            GovernanceDomain.MODULE,
            safe_metadata={"label": "ok"},
        ),
    )
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v10_governance_mesh_profiles_total"] == 1
    assert mesh.audit() and mesh.traces() and mesh.structured_logs()
    assert mesh.diagnostics()["runtime_mutation"] is False
    snapshot = dashboard_snapshot(mesh)
    assert len(DASHBOARD_SECTIONS) == 13
    assert snapshot["read_only"] is True and snapshot["actions"] == ()
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(ValueError, match="secret-bearing"):
        mesh.register(
            "profiles",
            GovernanceProfile(
                "bad",
                "s",
                SubjectType.MODULE,
                GovernanceDomain.MODULE,
                safe_metadata={"token": "x"},
            ),
        )
    assert mesh.serialize({"password": "x"}) == {"password": "[REDACTED]"}


def test_api_and_openapi_are_get_only_and_integrated() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    source = (Path(__file__).resolve().parents[3] / "server/api/app.py").read_text()
    assert "register_v10_sovereign_governance_mesh_routes(app)" in source


def test_no_action_or_mutation_capabilities() -> None:
    mesh = SovereignGovernanceMesh()
    overview = mesh.overview()
    assert overview["execution"] == "disabled"
    assert overview["automatic_approval"] is False
    forbidden = (
        "execute",
        "apply",
        "approve",
        "mutate",
        "publish",
        "deploy",
        "upgrade",
        "migrate",
        "rollback",
        "browser",
        "tiktok",
    )
    assert not any(hasattr(mesh, name) for name in forbidden)
