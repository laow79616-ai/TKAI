"""Mock-only validation for the TikTok AI Intelligent Decision Center."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.decision_center import (
    DASHBOARD_SECTIONS,
    DECISION_INPUTS,
    Decision,
    DecisionScope,
    DecisionStatus,
    MockDecisionInputProvider,
    TikTokAIIntelligentDecisionCenter,
)
from tiktok.decision_center.api import ROUTES, register_decision_center_routes
from tiktok.decision_center.metrics import METRIC_NAMES
from tiktok.decision_center.models import utcnow


def scope(
    workspace: str = "workspace",
    permissions: frozenset[str] = frozenset({"tiktok:decision:admin"}),
) -> DecisionScope:
    return DecisionScope("tenant", workspace, "operator", permissions)


def decision(workspace: str = "workspace") -> Decision:
    return Decision(
        "decision-1",
        "Protect publishing reliability",
        "Review bounded capacity and risk evidence.",
        "tenant",
        workspace,
        "operator",
        2,
        metadata={"objective": "reliability"},
    )


def center() -> TikTokAIIntelligentDecisionCenter:
    return TikTokAIIntelligentDecisionCenter(MockDecisionInputProvider())


def analyzed() -> tuple[TikTokAIIntelligentDecisionCenter, DecisionScope]:
    service = center()
    decision_scope = scope()
    service.create(decision(), decision_scope)
    service.analyze("decision-1", decision_scope)
    return service, decision_scope


def recommended() -> tuple[TikTokAIIntelligentDecisionCenter, DecisionScope]:
    service, decision_scope = analyzed()
    recommendation = service.recommend(
        "decision-1",
        decision_scope,
        suggested_action="Review the approved publishing queue.",
        suggested_schedule="Next bounded maintenance window.",
        suggested_resources=["runtime-capacity-reference"],
        suggested_workflow="workflow-reference-only",
        suggested_recovery="Pause and return to the last approved checkpoint.",
        expected_outcome="Improved reliability within validated capacity.",
    )
    assert recommendation.advisory is True
    return service, decision_scope


def test_decision_model_and_lifecycle() -> None:
    service = center()
    item = service.create(decision(), scope())
    assert item.status is DecisionStatus.DRAFT
    evaluation = service.analyze(item.id, scope())
    assert item.status is DecisionStatus.ANALYZING
    assert 0 <= evaluation.confidence_score <= 1
    service.recommend(
        item.id,
        scope(),
        suggested_action="Review a bounded execution proposal.",
        suggested_schedule="Approved window only.",
        suggested_resources=["resource-reference"],
        suggested_workflow="workflow-reference",
        suggested_recovery="Pause safely.",
        expected_outcome="Reviewed proposal.",
    )
    assert item.status is DecisionStatus.PENDING_REVIEW
    service.review(
        item.id,
        f"recommendation-{item.id}",
        scope(),
        approved=True,
        notes="Approved after evidence review.",
        expires_at=utcnow() + timedelta(hours=1),
    )
    assert item.status is DecisionStatus.APPROVED
    service.transition(item.id, DecisionStatus.ARCHIVED, scope())
    service.transition(item.id, DecisionStatus.DELETED, scope())


def test_evaluation_covers_inputs_constraints_scores_and_encrypted_evidence() -> None:
    service, decision_scope = analyzed()
    evaluation = service.evaluations["evaluation-decision-1"]
    assert set(service.contexts["decision-1"].inputs) == set(DECISION_INPUTS)
    assert {item.name for item in evaluation.constraints} == {
        "minimum_confidence",
        "maximum_risk",
        "minimum_capacity",
    }
    assert all(item.passed for item in evaluation.constraints)
    assert len(evaluation.evidence_references) == len(DECISION_INPUTS)
    assert all(
        ref.startswith("sealed-ref://") for ref in evaluation.evidence_references
    )
    assert all(
        "mock://" not in item.reference
        for item in service.scoped(service.evidence.values(), decision_scope)
    )


def test_recommendations_are_advisory_and_block_unsafe_content() -> None:
    service, decision_scope = analyzed()
    with pytest.raises(ValueError, match="Unsafe"):
        service.recommend(
            "decision-1",
            decision_scope,
            suggested_action="captcha bypass",
            suggested_schedule="now",
            suggested_resources=[],
            suggested_workflow="unrestricted",
            suggested_recovery="none",
            expected_outcome="unsafe",
        )
    assert service.decisions["decision-1"].status is DecisionStatus.ANALYZING


def test_approval_requires_rbac_notes_expiration_and_creates_only_reference() -> None:
    service, decision_scope = recommended()
    with pytest.raises(PermissionError, match="approve"):
        service.review(
            "decision-1",
            "recommendation-decision-1",
            scope(permissions=frozenset({"tiktok:decision:read"})),
            approved=True,
            notes="reviewed",
            expires_at=utcnow() + timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="notes"):
        service.review(
            "decision-1",
            "recommendation-decision-1",
            decision_scope,
            approved=True,
            notes="",
            expires_at=utcnow() + timedelta(hours=1),
        )
    approval = service.review(
        "decision-1",
        "recommendation-decision-1",
        decision_scope,
        approved=True,
        notes="Evidence and constraints reviewed.",
        expires_at=utcnow() + timedelta(hours=1),
    )
    assert approval.execution_handoff_reference.startswith("sealed-ref://")
    assert not hasattr(service, "execute")


def test_workspace_isolation_audit_dashboard_analytics_and_metrics() -> None:
    service, decision_scope = recommended()
    assert service.scoped(service.decisions.values(), decision_scope)
    assert not service.scoped(service.decisions.values(), scope("other"))
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.analyze("decision-1", scope("other"))
    dashboard = service.dashboard(decision_scope)
    assert dashboard["sections"] == list(DASHBOARD_SECTIONS)
    assert dashboard["history"] >= 1
    assert dashboard["analytics"]["recommendations_total"] == 1
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_read_only_input_enforcement_restriction_stop_and_no_secrets() -> None:
    class WritableProvider(MockDecisionInputProvider):
        read_only = False

    with pytest.raises(ValueError, match="read-only"):
        TikTokAIIntelligentDecisionCenter(WritableProvider())

    class RestrictedProvider(MockDecisionInputProvider):
        def collect(self, value: DecisionScope) -> dict[str, dict[str, Any]]:
            result = super().collect(value)
            result["risk_state"]["restriction_active"] = True
            return result

    service = TikTokAIIntelligentDecisionCenter(RestrictedProvider())
    service.create(decision(), scope())
    with pytest.raises(PermissionError, match="restriction"):
        service.analyze("decision-1", scope())
    with pytest.raises(ValueError, match="Secrets"):
        center().create(
            Decision(
                "secret",
                "name",
                "description",
                "tenant",
                "workspace",
                "owner",
                1,
                metadata={"token": "forbidden"},
            ),
            scope(),
        )


def test_api_dashboard_openapi_contract_and_tiktok_only_regression() -> None:
    class FakeApp:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            assert kwargs["methods"] == ["GET"]
            self.paths.append(path)

    app = FakeApp()
    register_decision_center_routes(app, center())
    assert set(ROUTES).issubset(app.paths)
    assert "/tiktok/decision-center/evidence" in app.paths
    assert "/tiktok/decision-center/dashboard" in app.paths
    assert "/tiktok/decision-center/metrics" in app.paths
    contract = " ".join(app.paths).casefold()
    for unrelated in (
        "telegram",
        "whatsapp",
        "facebook",
        "instagram",
        "discord",
        "billing",
        "subscription",
        "licensing",
        "payment",
    ):
        assert unrelated not in contract
