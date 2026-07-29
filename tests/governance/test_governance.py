from __future__ import annotations

from typing import Any

import pytest

from governance import EnterpriseAIGovernancePlatform, GovernanceScope
from governance.api import register_governance_routes
from governance.dashboard import SECTIONS

PERMISSIONS = {
    "governance:read",
    "governance:policy:write",
    "governance:policy:approve",
    "governance:risk:write",
    "governance:compliance:write",
    "governance:approval:request",
    "governance:approval:decide",
    "governance:control:write",
    "governance:resource:write",
    "governance:incident:write",
    "governance:exception:write",
    "governance:evidence:write",
    "governance:report:read",
    "governance:report:export",
}


def configured() -> tuple[EnterpriseAIGovernancePlatform, GovernanceScope]:
    platform = EnterpriseAIGovernancePlatform()
    scope = GovernanceScope("tenant-a", "workspace-a", "alice")
    platform.security.grant(scope, PERMISSIONS)
    return platform, scope


def policy_payload() -> dict[str, Any]:
    return {
        "id": "policy-1",
        "name": "Approved model usage",
        "description": "Use approved models for production workloads.",
        "scope_type": "workspace",
        "scope_id": "workspace-a",
        "owner": "alice",
        "version": "3.2.0",
        "rules": [{"effect": "allow", "model": "model-1"}],
        "controls": ["model-allowlist"],
        "metadata": {"classification": "internal"},
    }


def test_policy_fields_lifecycle_and_metrics() -> None:
    platform, scope = configured()
    policy = platform.create_policy(policy_payload(), scope)
    assert policy.to_dict()["status"] == "draft"
    statuses = (
        "review",
        "approved",
        "active",
        "suspended",
        "deprecated",
        "archived",
    )
    for status in statuses:
        policy = platform.transition_policy(policy.id, status, scope)
    assert policy.status.value == "archived"
    metrics = platform.metrics.snapshot()
    assert metrics["governance_policies_total"] == 1
    assert metrics["governance_active_policies"] == 0
    with pytest.raises(ValueError, match="Invalid policy transition"):
        platform.transition_policy(policy.id, "review", scope)


def test_risk_compliance_approvals_controls_and_reports() -> None:
    platform, scope = configured()
    policy = platform.create_policy(policy_payload(), scope)
    platform.create_risk(
        {
            "id": "risk-1",
            "category": "model",
            "likelihood": "high",
            "impact": "critical",
            "severity": "critical",
            "owner": "alice",
            "mitigation": "Require evaluation and approval.",
            "residual_risk": "medium",
        },
        scope,
    )
    platform.create_compliance_record(
        {
            "id": "mapping-1",
            "framework": "customer-control-framework",
            "control_mapping": {"AC-1": "model-allowlist"},
            "assessment": "review required",
            "finding": "Evidence is incomplete.",
            "remediation": "Attach evaluation evidence.",
            "attestation": "owner-reviewed",
        },
        scope,
    )
    approval = platform.request_approval(
        {
            "id": "approval-1",
            "resource_type": "policy",
            "resource_id": policy.id,
            "reason": "Production activation",
        },
        scope,
    )
    assert platform.decide_approval(approval.id, "approved", scope).approver == "alice"
    platform.create_control(
        {
            "id": "control-1",
            "control_type": "model_allowlist",
            "name": "Production model allowlist",
            "configuration": {"api_key": "must-not-appear"},
        },
        scope,
    )
    report = platform.report(scope)
    assert report["risk_summary"]["critical"] == 1
    assert report["open_findings"] == 1
    assert "do not constitute certification" in report["disclaimer"]


@pytest.mark.parametrize(
    ("kind", "attributes"),
    [
        (
            "model",
            {
                "provider": "provider-a",
                "allowed_use": ["support"],
                "restricted_use": ["medical"],
                "fallback_policy": "deny",
                "evaluation_reference": "eval-1",
            },
        ),
        (
            "prompt",
            {
                "risk_classification": "medium",
                "sensitive_variables": ["customer_id"],
                "change_history": ["v1"],
            },
        ),
        (
            "agent",
            {
                "tools": ["search"],
                "permissions": ["read"],
                "memory_policy": "session",
                "execution_limits": {"turns": 10},
                "delegation_limits": {"depth": 1},
            },
        ),
        (
            "application",
            {
                "components": ["agent-1"],
                "permissions": ["run"],
                "data_access": ["dataset-1"],
                "deployment_status": "staged",
            },
        ),
        (
            "workflow",
            {
                "nodes": ["start"],
                "connectors": ["http"],
                "secrets": ["secret-ref"],
                "execution_limits": {"seconds": 60},
                "approvals": ["approval-1"],
            },
        ),
        (
            "dataset",
            {
                "classification": "confidential",
                "retention": "30d",
                "access": ["analyst"],
                "export_policy": "deny",
                "deletion_policy": "verified",
            },
        ),
        (
            "knowledge_base",
            {
                "classification": "internal",
                "retention": "365d",
                "access": ["employee"],
                "export_policy": "review",
                "deletion_policy": "verified",
            },
        ),
    ],
)
def test_governed_resource_contracts(kind: str, attributes: dict[str, Any]) -> None:
    platform, scope = configured()
    item = platform.register_resource(
        kind,
        {
            "id": f"{kind}-1",
            "version": "3.2.0",
            "owner": "alice",
            "attributes": attributes,
        },
        scope,
    )
    assert item.kind == kind
    assert item.approval_status.value == "pending"


def test_incidents_exceptions_immutable_evidence_and_redacted_export() -> None:
    platform, scope = configured()
    platform.create_policy(policy_payload(), scope)
    platform.create_incident(
        {
            "id": "incident-1",
            "severity": "high",
            "source": "monitor",
            "affected_resource": "model-1",
            "timeline": [{"at": "now", "event": "detected"}],
            "containment": "Suspended model.",
            "resolution": "Pending.",
        },
        scope,
    )
    platform.create_exception(
        {
            "id": "exception-1",
            "policy_id": "policy-1",
            "scope": "application:demo",
            "reason": "Migration",
            "approver": "security-owner",
            "expiration": "2026-08-31T00:00:00Z",
            "compensating_control": "Manual review",
        },
        scope,
    )
    platform.record_evidence(
        {
            "id": "evidence-1",
            "evidence_type": "configuration_snapshot",
            "reference": "audit://snapshot/1",
            "resource_id": "model-1",
            "checksum": "sha256:abc",
        },
        scope,
    )
    with pytest.raises(ValueError, match="already exists"):
        platform.record_evidence(
            {
                "id": "evidence-1",
                "evidence_type": "test_result",
                "reference": "audit://test/2",
                "resource_id": "model-1",
                "checksum": "sha256:def",
            },
            scope,
        )
    assert platform.export_audit(scope)[0]["reference"] == "audit://snapshot/1"
    platform.security.max_export_records = 0
    with pytest.raises(ValueError, match="bounded export"):
        platform.export_audit(scope)


def test_tenant_workspace_rbac_and_sensitive_metadata_redaction() -> None:
    platform, scope = configured()
    platform.create_policy(
        {
            **policy_payload(),
            "metadata": {
                "token": "secret-value",
                "nested": {"password": "secret-value"},
            },
        },
        scope,
    )
    other_tenant = GovernanceScope("tenant-b", "workspace-a", "alice")
    platform.security.grant(other_tenant, PERMISSIONS)
    with pytest.raises(PermissionError, match="Cross-tenant"):
        platform._get(platform.policies, "policy-1", other_tenant)
    other_workspace = GovernanceScope("tenant-a", "workspace-b", "alice")
    platform.security.grant(other_workspace, PERMISSIONS)
    with pytest.raises(PermissionError, match="Cross-workspace"):
        platform._get(platform.policies, "policy-1", other_workspace)
    unprivileged = GovernanceScope("tenant-a", "workspace-a", "bob")
    with pytest.raises(PermissionError, match="governance:policy:write"):
        platform.create_policy({**policy_payload(), "id": "policy-2"}, unprivileged)
    redacted = platform.security.redact(platform.policies["policy-1"].to_dict())
    assert redacted["metadata"]["token"] == "[REDACTED]"
    assert redacted["metadata"]["nested"]["password"] == "[REDACTED]"


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_dashboard_and_metrics_contract() -> None:
    platform, scope = configured()
    app = App()
    register_governance_routes(app, platform)
    for path in (
        "/governance/policies",
        "/governance/risks",
        "/governance/compliance",
        "/governance/approvals",
        "/governance/controls",
        "/governance/models",
        "/governance/prompts",
        "/governance/agents",
        "/governance/applications",
        "/governance/workflows",
        "/governance/data",
        "/governance/incidents",
        "/governance/exceptions",
        "/governance/reports",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    assert set(SECTIONS) == set(platform.dashboard(scope)["sections"])
    for metric in platform.metrics.values:
        assert metric in platform.metrics.render_prometheus()
