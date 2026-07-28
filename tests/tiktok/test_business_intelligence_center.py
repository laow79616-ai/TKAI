"""Offline tests for the Enterprise TikTok Business Intelligence Center."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.business_intelligence_center import (
    BIScope,
    BIWorkspace,
    BoundedTestDouble,
    BusinessScope,
    Dataset,
    Insight,
    IntegrityStatus,
    Metric,
    Query,
    TikTokBusinessIntelligenceCenter,
    WorkspaceStatus,
)
from tiktok.business_intelligence_center.api import ROUTES
from tiktok.business_intelligence_center.metrics import METRIC_NAMES


def scope(workspace: str = "w1", permissions: frozenset[str] | None = None) -> BIScope:
    effective = (
        frozenset({"tiktok:business-intelligence:admin"})
        if permissions is None
        else permissions
    )
    return BIScope("tenant", workspace, "operator", effective)


def workspace(identifier: str = "bi1", name: str = "Enterprise BI") -> BIWorkspace:
    return BIWorkspace(
        identifier,
        name,
        "Unified analytics",
        "tenant",
        "w1",
        "owner",
        BusinessScope.PLATFORM,
    )


def dataset(identifier: str = "d1") -> Dataset:
    now = datetime.now(timezone.utc)
    return Dataset(
        identifier,
        "tenant",
        "w1",
        "lead_center",
        "ref://lead/analytics",
        "ref://schema/leads",
        now - timedelta(days=7),
        now,
        "daily",
        60,
        1,
        IntegrityStatus.VALID,
        "encrypted://datasets/d1",
    )


def test_lifecycle_rbac_and_isolation() -> None:
    service = TikTokBusinessIntelligenceCenter()
    service.create_workspace(workspace(), scope())
    assert service.transition("bi1", WorkspaceStatus.COLLECTING, scope()).version == 2
    with pytest.raises(ValueError):
        service.transition("bi1", WorkspaceStatus.APPROVED, scope())
    assert service.scoped_values(service.workspaces.values(), scope("other")) == []
    with pytest.raises(PermissionError):
        service.create_workspace(workspace("bi2"), scope(permissions=frozenset()))


def test_dataset_integrity_consent_purpose_and_references() -> None:
    service = TikTokBusinessIntelligenceCenter()
    service.register_dataset(dataset(), scope())
    invalid = dataset("d2")
    invalid.integrity_status = IntegrityStatus.INVALID
    with pytest.raises(ValueError):
        service.register_dataset(invalid, scope())
    no_consent = dataset("d3")
    no_consent.consent_aware = False
    with pytest.raises(PermissionError):
        service.register_dataset(no_consent, scope())


def test_bounded_query_masking_and_protected_rejection() -> None:
    now = datetime.now(timezone.utc)
    service = TikTokBusinessIntelligenceCenter(
        BoundedTestDouble([{"workspace": "w1", "email": "a@example.com", "count": 2}])
    )
    service.register_dataset(dataset(), scope())
    result = service.execute_query(
        Query(
            "q1",
            "tenant",
            "w1",
            "d1",
            dimensions=["workspace"],
            time_start=now - timedelta(days=1),
            time_end=now,
            page_size=10,
            row_limit=10,
        ),
        scope(),
    )
    assert result["read_only"] and result["rows"][0]["email"] == "***"
    with pytest.raises(ValueError):
        service.execute_query(
            Query(
                "q2", "tenant", "w1", "d1", page_size=501, time_start=now, time_end=now
            ),
            scope(),
        )
    protected = TikTokBusinessIntelligenceCenter(
        BoundedTestDouble([{"race": "prohibited"}])
    )
    protected.register_dataset(dataset(), scope())
    with pytest.raises(ValueError, match="Protected"):
        protected.execute_query(
            Query("q3", "tenant", "w1", "d1", time_start=now, time_end=now), scope()
        )


def test_metrics_forecasts_insights_exports_dashboard_and_routes() -> None:
    service = TikTokBusinessIntelligenceCenter()
    service.register_dataset(dataset(), scope())
    service.register_metric(
        Metric(
            "m1",
            "tenant",
            "w1",
            "Leads",
            "Qualified leads",
            "count",
            "leads",
            "owner",
            "ref://target/1",
            "ref://threshold/1",
        ),
        scope(),
    )
    forecast = service.create_artifact(
        "forecast",
        "f1",
        {
            "confidence": 0.8,
            "evidence_references": ["ref://snapshot/1"],
            "window": "30d",
        },
        scope(),
    )
    assert forecast["advisory"]
    insight = Insight(
        "i1",
        "tenant",
        "w1",
        "Lead trend",
        "Volume increased",
        "leads",
        "info",
        0.9,
        ["ref://trend/1"],
        recommended_review="Review capacity",
    )
    service.add_insight(insight, scope())
    exported = service.export(
        "e1", {"rows": [{"count": 1}]}, "csv", scope(), row_limit=10
    )
    assert exported["authorized"] and exported["audit"]
    assert service.dashboard(scope())["safety"]["direct_execution"] is False
    assert service.analytics(scope())["arbitrary_sql"] is False
    assert "/tiktok/business-intelligence/governance" in ROUTES
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_metadata_and_export_authorization() -> None:
    service = TikTokBusinessIntelligenceCenter()
    bad = workspace()
    bad.metadata = {"race": "prohibited"}
    with pytest.raises(ValueError, match="Protected"):
        service.create_workspace(bad, scope())
    with pytest.raises(PermissionError):
        service.export(
            "e",
            {"rows": []},
            "json",
            scope(permissions=frozenset({"tiktok:business-intelligence:read"})),
        )
    with pytest.raises(ValueError):
        service.export("e", {"rows": []}, "xlsx", scope())
