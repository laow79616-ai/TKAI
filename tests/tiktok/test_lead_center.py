"""Offline coverage for the Enterprise TikTok Lead Management Center."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.lead_center import (
    Assignment,
    ConsentRecord,
    ConsentStatus,
    FollowUp,
    Handoff,
    HandoffTarget,
    Lead,
    LeadScope,
    LeadSource,
    LeadStatus,
    Qualification,
    TikTokLeadManagementCenter,
)
from tiktok.lead_center.api import ROUTES
from tiktok.lead_center.metrics import METRIC_NAMES


def scope(workspace: str = "w1") -> LeadScope:
    return LeadScope("tenant", workspace, "operator", frozenset({"tiktok:leads:admin"}))


def lead(identifier: str = "l1", workspace: str = "w1") -> Lead:
    return Lead(
        identifier,
        "Acme Creator",
        "tenant",
        workspace,
        "owner",
        LeadSource.MANUAL_ENTRY,
        "ref://manual/1",
        tiktok_public_reference=f"tiktok-public://{identifier}",
    )


def test_crud_lifecycle_scope_and_rbac() -> None:
    service = TikTokLeadManagementCenter()
    item = service.create_lead(lead(), scope())
    assert service.transition(item.id, LeadStatus.VALIDATED, scope()).version == 2
    with pytest.raises(ValueError):
        service.transition(item.id, LeadStatus.CONVERTED, scope())
    assert service.scoped_values(service.leads.values(), scope("other")) == []
    with pytest.raises(PermissionError):
        service.create_lead(lead("l2"), LeadScope("tenant", "w1", "x"))


def test_import_preview_limits_schema_and_duplicates() -> None:
    service = TikTokLeadManagementCenter()
    service.create_lead(lead(), scope())
    payload = "lead_id,name,public\nl2,Acme Creator,tiktok-public://l1\n"
    preview = service.preview_import(
        payload,
        "csv",
        {"lead_id": "id", "name": "display_name", "public": "tiktok_public_reference"},
        scope(),
    )
    assert preview["valid_rows"] == 1
    assert preview["duplicates"][0][0]["confidence"] == 1.0
    with pytest.raises(ValueError):
        service.preview_import(payload * 1001, "csv", {"lead_id": "id"}, scope())
    with pytest.raises(ValueError):
        service.preview_import('[{"id":"1"}]', "xml", {}, scope())


def test_manual_merge_proposal_never_auto_merges() -> None:
    service = TikTokLeadManagementCenter()
    service.create_lead(lead(), scope())
    service.create_lead(lead("l2"), scope())
    proposal = service.propose_merge("l1", "l2", scope())
    assert proposal["automatic_merge"] is False
    assert proposal["status"] == "manual_review_required"


def test_qualification_and_explainable_scoring_reject_sensitive_data() -> None:
    service = TikTokLeadManagementCenter()
    service.create_lead(lead(), scope())
    result = service.qualify(
        Qualification(
            "q1",
            "l1",
            "tenant",
            "w1",
            True,
            "Business campaign fit",
            0.9,
            0.8,
            0.5,
            0.7,
            ["campaign://approved/1"],
        ),
        scope(),
    )
    assert result.qualified
    score = service.score(
        "l1",
        scope(),
        business_fit=0.9,
        engagement_reference=0.7,
        recency=0.8,
        source_quality=1.0,
    )
    assert score.explanation and score.consent_state == 0
    with pytest.raises(ValueError, match="Protected"):
        service.update_lead("l1", {"metadata": {"race": "prohibited"}}, scope())


def test_assignment_consent_followup_and_suppression() -> None:
    service = TikTokLeadManagementCenter()
    item = service.create_lead(lead(), scope())
    item.status = LeadStatus.QUALIFIED
    assignment = Assignment(
        "a1",
        "l1",
        "tenant",
        "w1",
        "owner2",
        "operator",
        "reviewer",
        "ref://assignment/rule",
        10,
        80,
    )
    service.assign(assignment, scope())
    followup = FollowUp(
        "f1",
        "l1",
        "tenant",
        "w1",
        "Manual review call",
        datetime.now(timezone.utc) + timedelta(days=1),
        "owner2",
        80,
        "ref://channel/call",
        "ref://template/1",
    )
    with pytest.raises(PermissionError, match="Consent"):
        service.plan_followup(followup, scope())
    service.record_consent(
        ConsentRecord(
            "c1",
            "l1",
            "tenant",
            "w1",
            ConsentStatus.GRANTED,
            "approved_form",
            "sales_follow_up",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc) + timedelta(days=30),
        ),
        scope(),
    )
    assert service.plan_followup(followup, scope()).status == "proposed"
    service.record_consent(
        ConsentRecord(
            "c2",
            "l1",
            "tenant",
            "w1",
            ConsentStatus.WITHDRAWN,
            "user_request",
            "sales_follow_up",
            datetime.now(timezone.utc),
            withdrawal_reason="withdrawn",
        ),
        scope(),
    )
    with pytest.raises(PermissionError):
        service.plan_followup(
            FollowUp(
                "f2",
                "l1",
                "tenant",
                "w1",
                "No",
                datetime.now(timezone.utc),
                "owner",
                50,
                "ref://channel/call",
                "ref://template/1",
            ),
            scope(),
        )


def test_approval_gated_reference_only_handoff_dashboard_metrics() -> None:
    service = TikTokLeadManagementCenter()
    service.create_lead(lead(), scope())
    item = Handoff(
        "h1",
        "l1",
        "tenant",
        "w1",
        HandoffTarget.WORKFLOW_CENTER,
        "ref://lead/l1",
        False,
    )
    with pytest.raises(PermissionError):
        service.handoff(item, scope())
    item.approved = True
    assert service.handoff(item, scope()).receipt_reference.startswith("ref://")
    dashboard = service.dashboard(scope())
    assert dashboard["safety"]["direct_outreach_execution"] is False
    assert "/tiktok/leads/analytics" in ROUTES
    assert set(METRIC_NAMES) <= set(service.metrics.render_prometheus().split())
