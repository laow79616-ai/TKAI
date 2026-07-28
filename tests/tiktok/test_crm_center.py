from datetime import datetime, timezone

import pytest

from tiktok.crm_center import (
    Activity,
    ConsentRecord,
    ConsentStatus,
    Contact,
    CRMRecord,
    CRMScope,
    CRMStatus,
    FollowUp,
    Opportunity,
    Organization,
    Relationship,
    TikTokCRMCenter,
)
from tiktok.crm_center.api import ROUTES
from tiktok.crm_center.metrics import METRIC_NAMES


@pytest.fixture
def scope() -> CRMScope:
    return CRMScope(
        "tenant-a", "workspace-a", "operator", frozenset({"tiktok:crm:admin"})
    )


@pytest.fixture
def center(scope: CRMScope) -> TikTokCRMCenter:
    service = TikTokCRMCenter()
    service.create_record(
        CRMRecord(
            "crm-1",
            "Approved Business",
            scope.tenant,
            scope.workspace,
            scope.actor,
            lead_reference="ref://lead/lead-1",
        ),
        scope,
    )
    return service


def test_lifecycle_and_history(center: TikTokCRMCenter, scope: CRMScope) -> None:
    for state in (
        CRMStatus.QUALIFIED,
        CRMStatus.ACTIVE,
        CRMStatus.OPPORTUNITY,
        CRMStatus.NEGOTIATION,
        CRMStatus.WON,
        CRMStatus.ARCHIVED,
        CRMStatus.DELETED,
    ):
        center.transition("crm-1", state, scope)
    assert center.records["crm-1"].version == 8
    assert center.analytics(scope)["conversion_rate"] == 0.0
    assert len(center.history(scope)) == 8


def test_business_records_and_analytics(
    center: TikTokCRMCenter, scope: CRMScope
) -> None:
    center.add_organization(
        Organization("org-1", scope.tenant, scope.workspace, "Profile", "Retail", "US"),
        scope,
    )
    center.add_contact(
        Contact(
            "contact-1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            "Public Contact",
            public_tiktok_reference="tiktok-public://person/1",
        ),
        scope,
    )
    center.add_relationship(
        Relationship(
            "rel-1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            lead_reference="ref://lead/1",
            campaign_reference="ref://campaign/1",
        ),
        scope,
    )
    center.add_opportunity(
        Opportunity(
            "opp-1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            "Renewal",
            "qualified",
            value_reference="encrypted://value/1",
            probability=0.5,
        ),
        scope,
    )
    center.add_activity(
        Activity(
            "act-1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            "manual_note",
            note="Met at approved event",
        ),
        scope,
    )
    result = center.analytics(scope)
    assert result["organizations"] == result["contacts"] == result["opportunities"] == 1
    assert result["activities"] == 1


def test_consent_and_approval_gate_followup(
    center: TikTokCRMCenter, scope: CRMScope
) -> None:
    followup = FollowUp(
        "follow-1",
        "crm-1",
        scope.tenant,
        scope.workspace,
        "Prepare proposal",
        datetime.now(timezone.utc),
        scope.actor,
        True,
    )
    with pytest.raises(PermissionError):
        center.propose_followup(followup, scope)
    center.record_consent(
        ConsentRecord(
            "consent-1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            ConsentStatus.GRANTED,
            "business follow-up",
            datetime.now(timezone.utc),
        ),
        scope,
    )
    center.propose_followup(followup, scope)
    assert followup.status == "awaiting_approval"
    with pytest.raises(PermissionError):
        center.handoff_followup(followup.id, scope)
    followup.approved = True
    assert center.handoff_followup(followup.id, scope).startswith("ref://crm-workflow/")


def test_withdrawal_suppresses_followups(
    center: TikTokCRMCenter, scope: CRMScope
) -> None:
    now = datetime.now(timezone.utc)
    center.record_consent(
        ConsentRecord(
            "c1",
            "crm-1",
            scope.tenant,
            scope.workspace,
            ConsentStatus.GRANTED,
            "business",
            now,
        ),
        scope,
    )
    item = FollowUp(
        "f1",
        "crm-1",
        scope.tenant,
        scope.workspace,
        "Manual review",
        now,
        scope.actor,
        True,
        approved=True,
    )
    center.propose_followup(item, scope)
    center.record_consent(
        ConsentRecord(
            "c2",
            "crm-1",
            scope.tenant,
            scope.workspace,
            ConsentStatus.WITHDRAWN,
            "business",
            now,
            withdrawal="requested",
            suppression=True,
        ),
        scope,
    )
    assert item.status == "suppressed"
    with pytest.raises(PermissionError):
        center.handoff_followup(item.id, scope)


def test_isolation_rbac_and_sensitive_data(
    center: TikTokCRMCenter, scope: CRMScope
) -> None:
    other = CRMScope("tenant-b", "workspace-a", "reader")
    assert center.scoped_values(center.records.values(), other) == []
    with pytest.raises(ValueError):
        center.create_record(
            CRMRecord(
                "x",
                "X",
                scope.tenant,
                scope.workspace,
                scope.actor,
                metadata={"token": "bad"},
            ),
            scope,
        )


def test_dashboard_metrics_and_api_contract(
    center: TikTokCRMCenter, scope: CRMScope
) -> None:
    dashboard = center.dashboard(scope)
    assert dashboard["outreach_execution"] is False
    assert set(METRIC_NAMES) == set(center.metrics.values)
    assert ROUTES == (
        "/tiktok/crm/organizations",
        "/tiktok/crm/contacts",
        "/tiktok/crm/opportunities",
        "/tiktok/crm/activities",
        "/tiktok/crm/followups",
        "/tiktok/crm/analytics",
    )
