"""API management packaging and preservation tests."""

from pathlib import Path


def test_structure_docs_deployment_release_frontend_and_preserved_platforms() -> None:
    root = Path(__file__).resolve().parents[2]
    modules = (
        "gateways",
        "apis",
        "routes",
        "versions",
        "policies",
        "authentication",
        "authorization",
        "keys",
        "tokens",
        "quotas",
        "rate_limits",
        "transformations",
        "caching",
        "analytics",
        "developer_portal",
        "subscriptions",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (root / "api_management" / module / "__init__.py").is_file()
    for name in (
        "Architecture",
        "APILifecycle",
        "Gateway",
        "Versioning",
        "Policies",
        "Authentication",
        "Authorization",
        "RateLimits",
        "Quotas",
        "Caching",
        "DeveloperPortal",
        "Subscriptions",
        "Analytics",
        "Security",
        "Operations",
    ):
        assert (root / "docs" / "api_management" / f"{name}.md").is_file()
    assert "api_management*" in (root / "pyproject.toml").read_text(encoding="utf-8")
    assert (root / "Dockerfile.api").is_file()
    assert (root / "deployment" / "helm" / "tkai").is_dir()
    assert (root / ".github" / "workflows").is_dir()
    assert "api-management" in (
        root / "dashboard" / "frontend" / "src" / "App.tsx"
    ).read_text(encoding="utf-8")
    for preserved in (
        "integration_platform",
        "automation_platform",
        "operations_platform",
        "security_platform",
        "model_platform",
        "data_platform",
        "governance",
        "collaboration",
        "reasoning_engine",
        "memory_engine",
        "orchestrator",
        "app_store",
        "workflow_platform",
        "knowledge_platform",
        "applications",
        "enterprise",
        "cloud",
        "studio",
        "marketplace",
    ):
        assert (root / preserved).is_dir()
