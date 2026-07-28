"""Offline coverage for the TikTok Customer Journey Center."""

from datetime import datetime, timezone

import pytest

from tiktok.customer_journey import (
    ConsentState,
    Conversion,
    Handoff,
    HandoffTarget,
    Journey,
    JourneyScope,
    JourneyStage,
    JourneyStatus,
    Milestone,
    MilestoneState,
    Recommendation,
    Segment,
    TikTokCustomerJourneyCenter,
    Touchpoint,
)
from tiktok.customer_journey.api import ROUTES
from tiktok.customer_journey.metrics import METRIC_NAMES


def scope(workspace: str = "workspace-a") -> JourneyScope:
    return JourneyScope(
        "tenant-a",
        workspace,
        "operator",
        frozenset({"tiktok:customer-journeys:admin"}),
    )


def journey(identifier: str = "journey-1") -> Journey:
    return Journey(
        identifier,
        "Creator acquisition",
        "tenant-a",
        "workspace-a",
        "owner",
        "encrypted://lead/1",
        "encrypted://crm/1",
        "ref://campaign/1",
    )


def test_journey_lifecycle_stage_history_scope_and_rbac() -> None:
    center = TikTokCustomerJourneyCenter()
    item = center.create_journey(journey(), scope())
    center.transition(
        item.id, JourneyStatus.AWARENESS, JourneyStage.AWARENESS, scope()
    )
    center.transition(item.id, JourneyStatus.INTEREST, JourneyStage.INTEREST, scope())
    assert item.version == 3
    assert len(center.history(scope())["stages"]) == 2
    assert center.scoped_values(center.journeys.values(), scope("other")) == []
    with pytest.raises(PermissionError):
        center.create_journey(
            journey("journey-2"),
            JourneyScope("tenant-a", "workspace-a", "reader"),
        )
    with pytest.raises(ValueError):
        center.transition(
            item.id, JourneyStatus.CONVERTED, JourneyStage.CONVERSION, scope()
        )


def test_touchpoints_milestones_and_custom_stage_are_bounded() -> None:
    center = TikTokCustomerJourneyCenter()
    center.create_journey(journey(), scope())
    point = Touchpoint(
        "touch-1",
        "journey-1",
        "tenant-a",
        "workspace-a",
        "campaign_reference",
        "ref://campaign/1",
        datetime.now(timezone.utc),
    )
    assert center.add_touchpoint(point, scope()) is point
    with pytest.raises(ValueError):
        center.add_milestone(
            Milestone(
                "mile-1",
                "journey-1",
                "tenant-a",
                "workspace-a",
                "Qualified",
                MilestoneState.MANUAL_OVERRIDE,
                datetime.now(timezone.utc),
            ),
            scope(),
        )
    center.transition(
        "journey-1",
        JourneyStatus.AWARENESS,
        JourneyStage.CUSTOM,
        scope(),
        custom_stage="First-party review",
    )


def test_recommendations_are_advisory_evidenced_and_consent_aware() -> None:
    center = TikTokCustomerJourneyCenter()
    center.create_journey(journey(), scope())
    center.add_segment(
        Segment(
            "segment-1",
            "journey-1",
            "tenant-a",
            "workspace-a",
            consent_state=ConsentState.SUPPRESSED,
        ),
        scope(),
    )
    with pytest.raises(PermissionError):
        center.recommend(
            Recommendation(
                "rec-1",
                "journey-1",
                "tenant-a",
                "workspace-a",
                "Propose manual review",
                0.8,
                ["ref://analytics/1"],
                suggested_follow_up_proposal="ref://followup/1",
            ),
            scope(),
        )
    recommendation = Recommendation(
        "rec-2",
        "journey-1",
        "tenant-a",
        "workspace-a",
        "Review campaign evidence",
        0.9,
        ["ref://analytics/2"],
        suggested_campaign="ref://campaign/2",
    )
    assert center.recommend(recommendation, scope()).advisory_only


def test_conversion_analytics_dashboard_metrics_and_history() -> None:
    center = TikTokCustomerJourneyCenter()
    center.create_journey(journey(), scope())
    center.record_conversion(
        Conversion(
            "conversion-1",
            "journey-1",
            "tenant-a",
            "workspace-a",
            "qualified_conversion",
            "encrypted://conversion/1",
            datetime.now(timezone.utc),
            "ref://analytics/attribution/1",
            "accepted",
        ),
        scope(),
    )
    analytics = center.analytics(scope())
    assert analytics["conversion_rate"] == 1.0
    dashboard = center.dashboard(scope())
    assert dashboard["safety"]["direct_outreach_execution"] is False
    assert set(METRIC_NAMES) <= set(center.metrics.render_prometheus().split())
    assert len(ROUTES) == 6
    assert center.history(scope())["conversions"][0]["outcome"] == "accepted"


def test_handoffs_require_approval_and_never_execute_outreach() -> None:
    center = TikTokCustomerJourneyCenter()
    center.create_journey(journey(), scope())
    handoff = Handoff(
        "handoff-1",
        "journey-1",
        "tenant-a",
        "workspace-a",
        HandoffTarget.WORKFLOW_CENTER,
        "ref://journey/1",
        False,
    )
    with pytest.raises(PermissionError):
        center.handoff(handoff, scope())
    handoff.approved = True
    assert center.handoff(handoff, scope()).receipt_reference.startswith("ref://")
