from pathlib import Path

from business_intelligence import (
    METRICS,
    BIScope,
    BusinessIntelligenceAPI,
    BusinessIntelligencePlatform,
)


def test_api_contract() -> None:
    api = BusinessIntelligenceAPI(BusinessIntelligencePlatform())
    scope = BIScope("tenant", "workspace", "actor")
    assert len(api.ROUTES) == 13
    assert "/business-intelligence/workspaces" in api.ROUTES
    assert api.get("/business-intelligence/dashboards", scope) == []


def test_release_structure_documentation_and_metrics() -> None:
    root = Path(__file__).parents[2]
    modules = (
        "workspaces",
        "data_sources",
        "datasets",
        "semantic_models",
        "metrics",
        "dimensions",
        "measures",
        "queries",
        "reports",
        "dashboards",
        "visualizations",
        "insights",
        "alerts",
        "subscriptions",
        "exports",
        "governance",
        "api",
        "dashboard",
    )
    for module in modules:
        assert (
            root / "business_intelligence" / module / "__init__.py"
        ).is_file()
    for document in (
        "Architecture",
        "WorkspaceLifecycle",
        "DataSources",
        "Datasets",
        "SemanticModels",
        "Metrics",
        "Queries",
        "Reports",
        "Visualizations",
        "Insights",
        "Alerts",
        "Subscriptions",
        "Governance",
        "Security",
        "Operations",
    ):
        assert (
            root / "docs" / "business_intelligence" / f"{document}.md"
        ).is_file()
    assert len(METRICS) == 11
    assert "business_intelligence*" in (root / "pyproject.toml").read_text(
        "utf-8"
    )
